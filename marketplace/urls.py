# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductImageViewSet, ProductViewSet, CategoryViewSet, BrandViewSet, AttributeViewSet, AttributeValueViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'attributes', AttributeViewSet, basename='attribute')
router.register(r'attribute-values', AttributeValueViewSet, basename='attribute-value')
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
    path('products/<int:product_pk>/images/', 
        ProductImageViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }), 
        name='product-images'
    ),
    # Add these if you want explicit URLs
    path('products/public/', ProductViewSet.as_view({'get': 'public_list'}), name='product-public-list'),
    path('products/category/<int:category_id>/', ProductViewSet.as_view({'get': 'by_category'}), name='product-by-category'),
    path('products/<int:pk>/public/', ProductViewSet.as_view({'get': 'public_detail'}), name='product-public-detail'),
    
]