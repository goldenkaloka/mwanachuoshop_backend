from django.urls import path
from .views import (
    BrandListView,
    CategoryListView,
    FilterOptionsView,
    ProductListCreateView,
    ProductRetrieveUpdateDestroyView,
    UserProductListView,
    InitiateSubscriptionPaymentAPI,
    InitiateProductPaymentAPI,
    azam_payment_callback,
    azam_product_payment_callback
)

urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),
    path('products/me/', UserProductListView.as_view(), name='user-product-list'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('payment/subscription/', InitiateSubscriptionPaymentAPI.as_view(), name='initiate-subscription-payment'),
    path('payment/product/', InitiateProductPaymentAPI.as_view(), name='initiate-product-payment'),
    
    path('webhook/azampay/', azam_payment_callback, name='azam-payment-callback'),
    path('webhook/azampay-product/', azam_product_payment_callback, name='azam-product-payment-callback'),
    path('products/filter-options/', FilterOptionsView.as_view(), name='filter-options'),
]