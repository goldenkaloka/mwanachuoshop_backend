from django.urls import include, path
from .views import (
    PaymentServiceViewSet, PaymentViewSet,
    create_product_payment, create_estate_payment,
    create_shop_subscription_payment, zenopay_callback,
    zenopay_callback_compatible
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'services', PaymentServiceViewSet)
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('create-product-payment/', create_product_payment, name='create-product-payment'),
    path('create-estate-payment/', create_estate_payment, name='create-estate-payment'),
    path('create-shop-subscription-payment/', create_shop_subscription_payment, name='create-shop-subscription-payment'),
    path('zenopay-callback/', zenopay_callback, name='zenopay-callback'),
    path('zenopay-callback-compatible/', zenopay_callback_compatible, name='zenopay-callback-compatible'),
    path('callback/zenopay/', zenopay_callback, name='zenopay-callback-legacy'),
]