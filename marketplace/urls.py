# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductImageViewSet, ProductViewSet, CategoryViewSet, BrandViewSet, AttributeViewSet, AttributeValueViewSet, WhatsAppClickView

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
    path('whatsapp-click/', WhatsAppClickView.as_view(), name='whatsapp-click'),
]
