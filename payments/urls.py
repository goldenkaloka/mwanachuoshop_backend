from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'payments', views.PaymentViewSet)

urlpatterns = [
    path('', views.create_product_payment, name='create_product_payment'),
    path('estate/', views.create_estate_payment, name='create_estate_payment'),
    path('subscription/', views.create_shop_subscription_payment, name='create_shop_subscription_payment'),
    path('callback/azampay/', views.azampay_callback, name='azampay_callback'),
    path('', include(router.urls)),
]