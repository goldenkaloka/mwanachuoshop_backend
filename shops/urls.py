from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet,
    ShopSubscriptionViewSet,
    ShopViewSet,
    ShopMediaViewSet,
    ShopServiceViewSet,
    ShopPromotionViewSet
)

router = DefaultRouter()
router.register(r'subscription-plans', SubscriptionPlanViewSet)
router.register(r'shop-subscriptions', ShopSubscriptionViewSet)
router.register(r'shops', ShopViewSet)
router.register(r'shop-media', ShopMediaViewSet)
router.register(r'shop-services', ShopServiceViewSet)
router.register(r'shop-promotions', ShopPromotionViewSet)

urlpatterns = router.urls