from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentServiceViewSet,
    PaymentViewSet,
    WalletViewSet,
    create_product_payment,
    create_estate_payment,
    create_shop_subscription_payment,
    create_brand_payment,
    pesapal_callback
)

router = DefaultRouter()
router.register(r'services', PaymentServiceViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'wallet', WalletViewSet)  # Register WalletViewSet

urlpatterns = [
    path('', include(router.urls)),
    path('v3/payments/', include('django_pesapalv3.urls')),  # Include Pesapal v3 API URLs
    path('create-product-payment/', create_product_payment, name='create-product-payment'),
    path('create-estate-payment/', create_estate_payment, name='create-estate-payment'),
    path('create-shop-subscription-payment/', create_shop_subscription_payment, name='create-shop-subscription-payment'),
    path('create-brand-payment/', create_brand_payment, name='create-brand-payment'),
    path('v3/payments/callback/pesapal/', pesapal_callback, name='pesapal-callback'),
]