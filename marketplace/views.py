from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch, Q, Count
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage
from .serializers import (
    CategorySerializer, BrandSerializer, AttributeSerializer,
    AttributeValueSerializer, ProductDetailSerializer,
    ProductListSerializer, ProductSerializer, ProductImageSerializer, WhatsAppClickSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsProductOwnerOrReadOnly
from .pagination import InfiniteScrollCursorPagination
from shops.models import Shop, UserOffer
from payments.models import Payment
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import logging
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone

logger = logging.getLogger(__name__)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return super().get_queryset().prefetch_related('children')

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category_id']

    def get_queryset(self):
        queryset = super().get_queryset()
        category_ids = self.request.query_params.get('category_id')
        if category_ids:
            try:
                category_ids = [int(cid) for cid in category_ids.split(',') if cid]
                queryset = queryset.filter(category_id__in=category_ids)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid category IDs: {category_ids}, error: {str(e)}")
                queryset = queryset.none()
        return queryset

class AttributeViewSet(viewsets.ModelViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

class AttributeValueViewSet(viewsets.ModelViewSet):
    serializer_class = AttributeValueSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category_id', 'attribute_id']

    def get_queryset(self):
        queryset = AttributeValue.objects.select_related('attribute', 'category')
        category_id = self.request.query_params.get('category_id')
        include_ancestors = self.request.query_params.get('include_ancestors', 'false').lower() == 'true'

        if category_id:
            try:
                category_id = int(category_id)
                if include_ancestors:
                    category = Category.objects.get(id=category_id)
                    ancestor_ids = category.get_ancestors(include_self=True).values_list('id', flat=True)
                    queryset = queryset.filter(category_id__in=ancestor_ids)
                else:
                    queryset = queryset.filter(category_id=category_id)
            except (Category.DoesNotExist, ValueError):
                queryset = queryset.none()
        return queryset

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = InfiniteScrollCursorPagination

    def get_queryset(self):
        queryset = Product.objects.select_related(
            'brand', 'category', 'owner', 'shop'
        ).prefetch_related(
            'images',
            Prefetch('attribute_values', queryset=AttributeValue.objects.select_related('attribute'))
        ).order_by('-created_at')

        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(owner=self.request.user) |
                Q(is_active=True, category__is_active=True) & (
                    Q(shop__isnull=True) |
                    Q(shop__subscription__status='active', shop__subscription__end_date__gt=timezone.now())
                )
            )

        if category_id := self.request.query_params.get('category'):
            try:
                queryset = queryset.filter(category__id=int(category_id))
            except (ValueError, TypeError):
                queryset = Product.objects.none()
        if brand_id := self.request.query_params.get('brand'):
            try:
                queryset = queryset.filter(brand__id=int(brand_id))
            except (ValueError, TypeError):
                queryset = Product.objects.none()

        return queryset

    def get_serializer_class(self):
        if self.action == 'recent' or self.action == 'by_category':
            return ProductListSerializer
        elif self.action == 'retrieve' or self.action == 'recent_detail':
            return ProductDetailSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        user = self.request.user
        shop = Shop.objects.filter(user=user).first()
        if not shop:
            logger.error(f"User {user.username} attempted product creation without a shop.")
            raise PermissionDenied("You must create a shop before adding products.")
        if shop.user != user:
            logger.error(f"Shop {shop.id} does not belong to user {user.username}.")
            raise PermissionDenied("Shop must belong to the product owner.")
        is_active = shop.is_subscription_active()
        instance = serializer.save(owner=user, shop=shop, is_active=is_active)
        logger.info(f"Product created for user {user.username}, shop: {shop.id}, is_active: {is_active}")

        if not is_active:
            return Response(
                {
                    "detail": "Product created but inactive. Use confirm_product_creation to activate.",
                    "product_id": instance.id
                },
                status=status.HTTP_201_CREATED
            )

    @action(detail=True, methods=['post'], url_path='confirm-product-creation',
            permission_classes=[permissions.IsAuthenticated])
    def confirm_product_creation(self, request, pk=None):
        with transaction.atomic():
            logger.info(f"Confirm product creation request: {request.data}")
            product_id = request.data.get('product_id', pk)
            transaction_id = request.data.get('transaction_id')

            if not product_id:
                logger.error("Product ID not provided in confirm-product-creation.")
                return Response(
                    {"error": "Product ID is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            product = get_object_or_404(Product, id=product_id, owner=request.user)

            if product.is_active:
                logger.info(f"Product {product_id} already active for user {request.user.username}.")
                return Response(
                    {"error": "Product is already active."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = request.user
            shop = product.shop
            offer = UserOffer.objects.filter(user=user).first()

            if product.check_shop_subscription():
                logger.info(f"Activating product {product_id} via active shop subscription or no shop.")
                product.is_active = True
                product.save()
                return Response(
                    {"detail": "Product activated.", "product_id": product.id},
                    status=status.HTTP_200_OK
                )

            if offer and offer.free_products_remaining > 0:
                logger.info(f"User {user.username} activating product {product_id} via free offer.")
                offer.free_products_remaining -= 1
                offer.save()
                product.is_active = True
                product.save()
                return Response(
                    {
                        "detail": "Product activated using free offer.",
                        "free_products_remaining": offer.free_products_remaining,
                        "product_id": product.id
                    },
                    status=status.HTTP_200_OK
                )

            if not transaction_id:
                payment_amount = max(
                    Decimal('1.00'),
                    (product.price * Decimal('0.001')).quantize(Decimal('0.01'))
                )
                logger.info(f"Payment required for product {product_id}: amount {payment_amount}.")
                return Response(
                    {
                        "payment_required": True,
                        "amount": str(payment_amount),
                        "product_id": product.id
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )

            try:
                payment = Payment.objects.select_for_update().get(
                    transaction_id=transaction_id,
                    status=Payment.PaymentStatus.COMPLETED,
                    user=user,
                    content_type=ContentType.objects.get_for_model(Product),
                    object_id=product.id
                )
                logger.info(f"Payment verified for product {product_id}, transaction_id {transaction_id}.")
                product.is_active = True
                product.save()
                return Response(
                    {"detail": "Product activated via payment.", "product_id": product.id},
                    status=status.HTTP_200_OK
                )
            except Payment.DoesNotExist:
                logger.error(f"No completed payment found for transaction_id {transaction_id}, product {product_id}.")
                return Response(
                    {"error": "Invalid or incomplete payment"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Payment verification failed for product {product_id}: {str(e)}")
                return Response(
                    {"error": "Payment processing error"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    @action(detail=False, permission_classes=[permissions.AllowAny])
    def recent(self, request):
        logger.info(f"Recent list query params: {request.query_params}")
        queryset = Product.objects.filter(
            Q(shop__isnull=True) | Q(shop__subscription__status='active', shop__subscription__end_date__gt=timezone.now()),
            category__is_active=True,
            is_active=True
        ).select_related(
            'brand', 'category', 'owner', 'shop'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('-is_primary')),
            Prefetch('attribute_values', queryset=AttributeValue.objects.select_related('attribute'))
        )

        if query := request.query_params.get('q'):
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__name__icontains=query) |
                Q(category__name__icontains=query)
            )

        if category_ids := self.request.query_params.get('category'):
            try:
                category_ids = [int(cid) for cid in category_ids.split(',') if cid]
                queryset = queryset.filter(category__id__in=category_ids)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid category IDs: {category_ids}, error: {str(e)}")
                return Response({
                    'next': None,
                    'previous': None,
                    'results': []
                })

        if brand_ids := self.request.query_params.get('brand'):
            try:
                brand_ids = [int(bid) for bid in brand_ids.split(',') if bid]
                queryset = queryset.filter(brand__id__in=brand_ids)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid brand IDs: {brand_ids}, error: {str(e)}")
                return Response({
                    'next': None,
                    'previous': None,
                    'results': []
                })

        if min_price := self.request.query_params.get('min_price'):
            try:
                min_price = Decimal(min_price)
                queryset = queryset.filter(price__gte=min_price)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid min_price: {min_price}, error: {str(e)}")

        if max_price := self.request.query_params.get('max_price'):
            try:
                max_price = Decimal(max_price)
                queryset = queryset.filter(price__lte=max_price)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid max_price: {max_price}, error: {str(e)}")

        if attribute_value_ids := self.request.query_params.get('attribute_value_ids'):
            try:
                attr_ids = [int(aid) for aid in attribute_value_ids.split(',')]
                for attr_id in attr_ids:
                    queryset = queryset.filter(attribute_values__id=attr_id)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid attribute_value_ids: {attribute_value_ids}, error: {str(e)}")
                return Response({
                    'next': None,
                    'previous': None,
                    'results': []
                })

        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering == 'price_low':
            queryset = queryset.order_by('price')
        elif ordering == 'price_high':
            queryset = queryset.order_by('-price')
        elif ordering == 'popular':
            queryset = queryset.annotate(
                click_count=Count('whatsapp_clicks')
            ).order_by('-click_count', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')

        logger.info(f"Recent queryset type before pagination: {type(queryset)}")
        page = self.paginate_queryset(queryset)
        logger.info(f"Recent page type after pagination: {type(page)}")
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        return Response({
            'next': None,
            'previous': None,
            'results': serializer.data
        })

    @action(detail=False, url_path='category/(?P<category_id>[^/.]+)',
            permission_classes=[permissions.AllowAny])
    def by_category(self, request, category_id=None):
        try:
            category = Category.objects.get(id=category_id, is_active=True)
        except (Category.DoesNotExist, ValueError):
            return Response({
                'next': None,
                'previous': None,
                'results': []
            }, status=status.HTTP_404_NOT_FOUND)

        queryset = Product.objects.filter(
            category=category,
            is_active=True,
        ).select_related(
            'brand', 'category', 'owner', 'shop'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('-is_primary'))
        ).order_by('-created_at')

        logger.info(f"By category queryset type: {type(queryset)}")
        page = self.paginate_queryset(queryset)
        logger.info(f"By category page type: {type(page)}")
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response({
                'category': CategorySerializer(category, context={'request': request}).data,
                'products': serializer.data
            })

        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        return Response({
            'category': CategorySerializer(category, context={'request': request}).data,
            'products': serializer.data
        })

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny], url_path='recent')
    def recent_detail(self, request, pk=None):
        try:
            pk = int(pk)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid product ID format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(
            Product.objects.filter(
                Q(shop__isnull=True) | Q(shop__subscription__status='active', shop__subscription__end_date__gt=timezone.now()),
                category__is_active=True,
                is_active=True
            ).select_related('brand', 'category', 'owner', 'shop').prefetch_related(
                'images',
                Prefetch('attribute_values', queryset=AttributeValue.objects.select_related('attribute'))
            ),
            id=pk
        )
        serializer = ProductDetailSerializer(product, context={'request': request})
        return Response(serializer.data)

class ProductImageViewSet(viewsets.ModelViewSet):
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsProductOwnerOrReadOnly]

    def get_queryset(self):
        return ProductImage.objects.filter(
            product_id=self.kwargs['product_pk'],
            product__owner=self.request.user
        )

    def perform_create(self, serializer):
        product = get_object_or_404(
            Product,
            id=self.kwargs['product_pk'],
            owner=self.request.user
        )
        serializer.save(product=product)

class WhatsAppClickView(APIView):
    def post(self, request):
        serializer = WhatsAppClickSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'click recorded'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)