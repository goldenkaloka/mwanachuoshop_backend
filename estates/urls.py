from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PropertyTypeViewSet,
    PropertyViewSet,
    PropertyImageViewSet,
    VideoViewSet
)

router = DefaultRouter()
router.register(r'property-types', PropertyTypeViewSet, basename='propertytype')
router.register(r'properties', PropertyViewSet, basename='property')
router.register(
    r'properties/(?P<property_slug>[-\w]+)/images',
    PropertyImageViewSet,
    basename='propertyimage'
)
router.register(
    r'properties/(?P<property_slug>[-\w]+)/videos',
    VideoViewSet,
    basename='video'
)
router.register(r'videos', VideoViewSet, basename='estate_video')

urlpatterns = [
    path('', include(router.urls)),
]