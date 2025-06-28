from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShopViewSet, ShopMediaViewSet, PromotionViewSet, EventViewSet, ServicesViewSet, UserOfferViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'', ShopViewSet, basename='shops')  # Changed from 'shops' to ''
router.register(r'shop-media', ShopMediaViewSet, basename='shop-media')
router.register(r'promotions', PromotionViewSet, basename='promotions')
router.register(r'events', EventViewSet, basename='events')
router.register(r'services', ServicesViewSet, basename='services')
router.register(r'offers', UserOfferViewSet, basename='offers')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscriptions')

urlpatterns = [
    path('', include(router.urls)),
]
