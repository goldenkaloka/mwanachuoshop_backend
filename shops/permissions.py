from rest_framework.permissions import BasePermission, SAFE_METHODS

from shops.models import Shop

class IsOwnerWithActiveSubscriptionOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if hasattr(obj, 'user'):
            is_owner = obj.user == request.user
        elif hasattr(obj, 'shop') and hasattr(obj.shop, 'user'):
            is_owner = obj.shop.user == request.user
        else:
            return False
        if is_owner:
            shop = obj if isinstance(obj, Shop) else obj.shop
            return shop.is_subscription_active()
        return False