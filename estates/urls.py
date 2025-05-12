from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, PropertyTypeViewSet, PropertyImageViewSet

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'property-types', PropertyTypeViewSet, basename='property-type')
router.register(r'property-images', PropertyImageViewSet, basename='property-image')

urlpatterns = [
    path('', include(router.urls)),
    # URL for serving the HLS playlist (master.m3u8 or similar)
    path('properties/<int:pk>/playlist/', PropertyViewSet.as_view({'get': 'serve_hls_playlist'}), name='property-playlist'),
    re_path(r'^properties/(?P<pk>\d+)/segments/(?P<segment_name>[^/]+\.ts)$', PropertyViewSet.as_view({'get': 'serve_hls_segment'}), name='property-segment'),
]
