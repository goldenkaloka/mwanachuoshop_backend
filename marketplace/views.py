from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch, Q, Count
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage
from .serializers import (
    CategorySerializer, BrandSerializer, AttributeSerializer,
    AttributeValueSerializer, ProductDetailSerializer,
    ProductListSerializer, ProductSerializer, ProductImageSerializer, WhatsAppClickSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsProductOwnerOrReadOnly
from .pagination import InfiniteScrollCursorPagination
from shops.models import Shop, UserOffer
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import logging
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.core.exceptions import ValidationError
# Location logic now handled by frontend - simplified approach
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from core.models import Campus
from drf_spectacular.utils import extend_schema
from rest_framework import serializers

logger = logging.getLogger(__name__)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('children')
        include_descendants = self.request.query_params.get('include_descendants', 'false').lower() == 'true'
        if include_descendants and self.request.query_params.get('id'):
            try:
                category_id = int(self.request.query_params.get('id'))
                category = Category.objects.get(id=category_id)
                descendant_ids = category.get_descendants(include_self=True).values_list('id', flat=True)
                queryset = queryset.filter(id__in=descendant_ids)
            except (Category.DoesNotExist, ValueError):
                queryset = queryset.none()
        return queryset

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_fields = []

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('categories')
        category_id = self.request.query_params.get('category_id')
        include_ancestors = self.request.query_params.get('include_ancestors', 'false').lower() == 'true'
        if category_id:
            try:
                category_id = int(category_id)
                valid_category_ids = {category_id}
                if include_ancestors:
                    category = Category.objects.get(id=category_id)
                    valid_category_ids.update(category.get_ancestors(include_self=False).values_list('id', flat=True))
                queryset = queryset.filter(categories__id__in=valid_category_ids).distinct()
            except (ValueError, Category.DoesNotExist) as e:
                logger.warning(f"Invalid category ID: {category_id}, error: {str(e)}")
                queryset = queryset.none()
        return queryset

class AttributeViewSet(viewsets.ModelViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category_id')
        include_ancestors = self.request.query_params.get('include_ancestors', 'false').lower() == 'true'
        if category_id:
            try:
                category_id = int(category_id)
                category = Category.objects.get(id=category_id)
                valid_category_ids = {category_id}
                if include_ancestors:
                    valid_category_ids.update(category.get_ancestors(include_self=False).values_list('id', flat=True))
                queryset = queryset.filter(values__category_id__in=valid_category_ids).distinct()
            except (Category.DoesNotExist, ValueError):
                queryset = queryset.none()
        return queryset

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
                category = Category.objects.get(id=category_id)
                valid_category_ids = {category_id}
                if include_ancestors:
                    valid_category_ids.update(category.get_ancestors(include_self=False).values_list('id', flat=True))
                queryset = queryset.filter(category_id__in=valid_category_ids)
            except (Category.DoesNotExist, ValueError):
                queryset = queryset.none()
        return queryset

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = InfiniteScrollCursorPagination

    def get_queryset(self):
        queryset = Product.objects.select_related('shop', 'owner', 'brand', 'category').prefetch_related('images', 'attribute_values')
        user = self.request.user
        now = timezone.now()
        
        if not user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        elif not user.is_staff:
            queryset = queryset.filter(
                (Q(owner=user)) |
                Q(is_active=True)
            )
        return queryset

    def get_serializer_class(self):
        if self.action == 'recent' or self.action == 'by_category':
            return ProductListSerializer
        elif self.action == 'retrieve' or self.action == 'recent_detail':
            return ProductDetailSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            user = self.request.user
            shop = Shop.objects.filter(user=user).first()
            offer = UserOffer.objects.filter(user=user).first()
            is_active = False

            if shop and shop.user != user:
                logger.error(f"Shop {shop.id} does not belong to user {user.username}.")
                raise PermissionDenied("Shop must belong to the product owner.")

            if shop and shop.is_subscription_active():
                is_active = True
                logger.info(f"Activating product via active shop subscription for user {user.username}.")
            elif offer and offer.free_products_remaining > 0:
                is_active = True
                offer.free_products_remaining -= 1
                offer.save()
                logger.info(f"Activating product via free offer for user {user.username}.")
            else:
                logger.info(f"Product created as inactive for user {user.username} - no active subscription or free offers.")

            # Remove location assignment logic
            # if not instance.location:
            #     from django.contrib.gis.geos import Point
            #     instance.location = Point(39.2695, -6.8235)  # Dar es Salaam center
            #     instance.save(update_fields=['location'])
            #     logger.info(f"Product {instance.id} assigned fallback coordinates - no location provided")

            # Campus ManyToMany assignment is handled by the serializer
            instance = serializer.save(
                owner=user,
                shop=shop,
                is_active=is_active
            )
            logger.info(f"Product {instance.id} created successfully")

            response_data = ProductSerializer(instance, context={'request': self.request}).data
            response_data['free_products_remaining'] = offer.free_products_remaining if offer else 0
            response_data['detail'] = "Product created and activated." if is_active else "Product created but not activated."
            logger.info(f"Product {instance.id} created for user {user.username}, is_active: {is_active}")
            return Response(response_data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        print("DEBUG: Raw request data:", request.data)
        print("DEBUG: Raw request FILES:", request.FILES)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("DEBUG: Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    @action(detail=False, permission_classes=[permissions.AllowAny])
    def recent(self, request):
        logger.info(f"Recent list query params: {request.query_params}")
        queryset = self.get_queryset()  # Now supports optional location filtering

        if query := self.request.query_params.get('q'):
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__name__icontains=query) |
                Q(category__name__icontains=query)
            )

        if category_ids := self.request.query_params.get('category'):
            try:
                category_ids = [int(cid) for cid in category_ids.split(',') if cid]
                include_descendants = self.request.query_params.get('include_descendants', 'false').lower() == 'true'
                valid_category_ids = set(category_ids)
                if include_descendants:
                    for cid in category_ids:
                        category = Category.objects.get(id=cid)
                        valid_category_ids.update(category.get_descendants(include_self=False).values_list('id', flat=True))
                queryset = queryset.filter(category__id__in=valid_category_ids)
            except (ValueError, TypeError, Category.DoesNotExist) as e:
                logger.warning(f"Invalid category IDs: {category_ids}, error: {str(e)}")
                return Response({'next': None, 'previous': None, 'results': []})

        if brand_ids := self.request.query_params.get('brand'):
            try:
                brand_ids = [int(bid) for bid in brand_ids.split(',') if bid]
                queryset = queryset.filter(brand__id__in=brand_ids)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid brand IDs: {brand_ids}, error: {str(e)}")
                return Response({'next': None, 'previous': None, 'results': []})

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
                return Response({'next': None, 'previous': None, 'results': []})

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

    @action(detail=False, url_path='category/(?P<category_id>[^/.]+)', permission_classes=[permissions.AllowAny])
    def by_category(self, request, category_id=None):
        try:
            category_id = int(category_id)
            category = Category.objects.get(id=category_id, is_active=True)
            valid_category_ids = {category_id}
            include_descendants = self.request.query_params.get('include_descendants', 'false').lower() == 'true'
            if include_descendants:
                valid_category_ids.update(category.get_descendants(include_self=False).values_list('id', flat=True))
        except (Category.DoesNotExist, ValueError):
            return Response({
                'next': None,
                'previous': None,
                'results': []
            }, status=status.HTTP_404_NOT_FOUND)

        queryset = self.get_queryset().filter(category__id__in=valid_category_ids)  # Now supports optional location filtering

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
            self.get_queryset(),  # Use get_queryset to apply public filters
            id=pk
        )
        serializer = ProductDetailSerializer(product, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_products(self, request):
        """
        Retrieve the authenticated user's products.
        """
        queryset = self.get_queryset().filter(owner=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def near_university(self, request):
        campus_id = request.query_params.get('campus_id')
        if not campus_id:
            return Response({'error': 'campus_id is required'}, status=400)
        try:
            campus = Campus.objects.get(id=campus_id)
        except Campus.DoesNotExist:
            return Response({'error': 'Campus not found'}, status=404)
        products = Product.objects.filter(
            campus=campus,
            is_active=True
        ).select_related('shop', 'owner', 'brand', 'category').prefetch_related('images')
        campus_data = {
            'id': campus.id,
            'name': campus.name,
            'latitude': campus.location.y if campus.location else None,
            'longitude': campus.location.x if campus.location else None
        }
        serializer = self.get_serializer(products, many=True)
        return Response({
            'campus': campus_data,
            'products': serializer.data
        })

    @action(detail=False, methods=['get'])
    def near_user(self, request):
        user = request.user
        radius = float(request.query_params.get('radius', 5000))
        # Remove location-based filtering and distance logic for products
        products = Product.objects.filter(
            is_active=True
        ).select_related('shop', 'owner', 'brand', 'category').prefetch_related('images')
        serializer = self.get_serializer(products, many=True)
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

class WhatsAppClickRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    message = serializers.CharField()

class WhatsAppClickResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()

@extend_schema(
    request=WhatsAppClickRequestSerializer,
    responses={200: WhatsAppClickResponseSerializer},
    description="Track WhatsApp click for a product."
)
class WhatsAppClickView(APIView):
    def post(self, request):
        serializer = WhatsAppClickSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'click recorded'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)