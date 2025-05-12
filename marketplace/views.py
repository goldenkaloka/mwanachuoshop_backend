from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch, Q
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage
from .serializers import (
    CategorySerializer, BrandSerializer, AttributeSerializer,
    AttributeValueSerializer, ProductDetailSerializer, 
    ProductListSerializer, ProductSerializer, ProductImageSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsProductOwnerOrReadOnly
from shops.models import Shop, UserOffer
from payments.models import Payment
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import logging

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
        category_id = self.request.query_params.get('category_id')
        if category_id:
            try:
                category_id = int(category_id)
                queryset = queryset.filter(category_id=category_id)
            except (ValueError, TypeError):
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

    def get_queryset(self):
        queryset = Product.objects.filter(
            owner=self.request.user
        ).select_related(
            'brand', 'category', 'owner'
        ).prefetch_related(
            'images',
            Prefetch('attribute_values', queryset=AttributeValue.objects.select_related('attribute'))
        )

        if category_id := self.request.query_params.get('category'):
            queryset = queryset.filter(category__id=category_id)
        if brand_id := self.request.query_params.get('brand'):
            queryset = queryset.filter(brand__id=brand_id)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        shop = Shop.objects.filter(user=user).first()
        # Create product with is_active=False by default
        serializer.save(owner=user, shop=shop, is_active=False)

    @action(detail=False, methods=['post'], url_path='confirm-product-creation', 
            permission_classes=[permissions.IsAuthenticated])
    def confirm_product_creation(self, request):
        """Activate a product using shop subscription, free offer, or payment"""
        with transaction.atomic():
            logger.info(f"Confirm product creation request: {request.data}")
            product_id = request.data.get('product_id')
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
            shop = Shop.objects.filter(user=user).first()
            offer = UserOffer.objects.filter(user=user).first()

            # Free activation paths
            if shop and shop.is_subscription_active():
                logger.info(f"User {user.username} activating product {product_id} via shop subscription.")
                product.is_active = True
                product.save()
                return Response(
                    {"detail": "Product activated via shop subscription."},
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
                        "free_products_remaining": offer.free_products_remaining
                    },
                    status=status.HTTP_200_OK
                )

            # Paid activation
            if not transaction_id:
                # Calculate payment amount: 0.1% of product price, minimum $1.00
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

            # Verify payment
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
                    {"detail": "Product activated via payment"},
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
        products = Product.objects.filter(
            category__is_active=True, is_active=True
        ).select_related(
            'brand', 'category', 'owner'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('-is_primary'))
        ).order_by('-created_at')[:50]

        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, permission_classes=[permissions.AllowAny])
    def public_list(self, request):
        queryset = Product.objects.filter(
            category__is_active=True, is_active=True
        ).select_related(
            'brand', 'category', 'owner'
        ).prefetch_related(
            'images',
            Prefetch('attribute_values', queryset=AttributeValue.objects.select_related('attribute'))
        )

        if query := request.query_params.get('q'):
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query) | 
                Q(brand__name__icontains=query) | Q(category__name__icontains=query)
            )
        if category_id := self.request.query_params.get('category'):
            queryset = queryset.filter(category__id=category_id)
        if brand_id := self.request.query_params.get('brand'):
            queryset = queryset.filter(brand__id=brand_id)
        if attribute_value_ids := self.request.query_params.get('attribute_value_ids'):
            try:
                attr_ids = [int(id) for id in attribute_value_ids.split(',')]
                for attr_id in attr_ids:
                    queryset = queryset.filter(attribute_values__id=attr_id)
            except (ValueError, TypeError):
                queryset = queryset.none()

        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, url_path='category/(?P<category_id>[^/.]+)', 
            permission_classes=[permissions.AllowAny])
    def by_category(self, request, category_id=None):
        category = get_object_or_404(Category, id=category_id, is_active=True)
        products = Product.objects.filter(
            category=category, is_active=True
        ).select_related(
            'brand', 'category', 'owner'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('-is_primary'))
        ).order_by('-created_at')

        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response({
            'category': CategorySerializer(category, context={'request': request}).data,
            'products': serializer.data
        })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def public_detail(self, request, pk=None):
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Invalid product ID format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(
            Product.objects.filter(category__is_active=True, is_active=True)
                .select_related('brand', 'category', 'owner')
                .prefetch_related(
                    'images',
                    Prefetch('attribute_values', 
                             queryset=AttributeValue.objects.select_related('attribute'))
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