from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch, Q
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage
from .serializers import (
    CategorySerializer, BrandSerializer, AttributeSerializer,
    AttributeValueSerializer, ProductDetailSerializer, 
    ProductListSerializer, ProductSerializer, ProductImageSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsProductOwnerOrReadOnly
from shops.models import Shop, UserOffer

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
    pagination_class = None  # Typically brands list is short

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
        """
        Return a queryset of AttributeValue objects, optimized with select_related.
        Optionally filter by category_id and include ancestors if requested.
        """
        queryset = AttributeValue.objects.select_related('attribute', 'category')

        # Filter by category_id from query params
        category_id = self.request.query_params.get('category_id')
        include_ancestors = self.request.query_params.get('include_ancestors', 'false').lower() == 'true'

        if category_id:
            try:
                category_id = int(category_id)
                if include_ancestors:
                    # Include attribute values from the category and its ancestors
                    try:
                        category = Category.objects.get(id=category_id)
                        ancestor_ids = category.get_ancestors(include_self=True).values_list('id', flat=True)
                        queryset = queryset.filter(category_id__in=ancestor_ids)
                    except Category.DoesNotExist:
                        queryset = queryset.none()  # Return empty queryset if category doesn't exist
                else:
                    # Filter by exact category_id
                    queryset = queryset.filter(category_id=category_id)
            except ValueError:
                queryset = queryset.none()  # Invalid category_id format

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
        offer = UserOffer.objects.filter(user=user).first()

        if offer and offer.free_products_remaining > 0:
            offer.free_products_remaining -= 1
            offer.save()

        serializer.save(owner=user, shop=shop)

    @action(detail=False, permission_classes=[permissions.AllowAny])
    def recent(self, request):
        """Get recently added products (last 10)"""
        products = Product.objects.filter(
            category__is_active=True
        ).select_related(
            'brand', 'category', 'owner'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('-is_primary'))
        ).order_by('-created_at')[:50]

        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, permission_classes=[permissions.AllowAny])
    def public_list(self, request):
        """Public product listing with optional attribute filtering"""
        queryset = Product.objects.filter(
            category__is_active=True,
        ).select_related(
            'brand', 'category', 'owner'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('-is_primary')),
            Prefetch('attribute_values', queryset=AttributeValue.objects.select_related('attribute'))
        )


        if query := request.query_params.get('q'):
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query) | Q(brand__name__icontains=query) 
                | Q(category__name__icontains=query) 
            )
        # Apply filters
        if category_id := request.query_params.get('category'):
            queryset = queryset.filter(category__id=category_id)
        if brand_id := request.query_params.get('brand'):
            queryset = queryset.filter(brand__id=brand_id)
        if attribute_value_ids := request.query_params.get('attribute_value_ids'):
            try:
                attr_ids = [int(id) for id in attribute_value_ids.split(',')]
                for attr_id in attr_ids:
                    queryset = queryset.filter(attribute_values__id=attr_id)
            except (ValueError, TypeError):
                queryset = queryset.none()  # Invalid attribute_value_ids format

        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, url_path='category/(?P<category_id>[^/.]+)', 
            permission_classes=[permissions.AllowAny])
    def by_category(self, request, category_id=None):
        """Products by category"""
        category = get_object_or_404(Category, id=category_id, is_active=True)
        products = Product.objects.filter(
            category=category, 
            is_active=True
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
        """Public product detail view"""
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Invalid product ID format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(
            Product.objects.filter(category__is_active=True)
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