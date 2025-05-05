# permissions.py
from rest_framework import permissions
from .models import Product, ProductImage

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS or
            request.user and request.user.is_staff
        )

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user

class IsProductOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            product_id = view.kwargs.get('product_pk')
            product = Product.objects.get(id=product_id)
            return product.owner == request.user
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.product.owner == request.user