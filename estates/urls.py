from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, PropertyTypeViewSet, PropertyImageViewSet, create_estate_payment

# Initialize the router
router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'property-types', PropertyTypeViewSet, basename='propertytype')
router.register(r'property-images', PropertyImageViewSet, basename='propertyimage')

# Define URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('create-estate-payment/', create_estate_payment, name='create-estate-payment'),
]