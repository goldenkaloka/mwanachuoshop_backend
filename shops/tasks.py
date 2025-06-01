# shops/tasks.py
from django.db import transaction
from django.utils import timezone
from .models import Subscription, Shop
from marketplace.models import Product
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def check_expired_subscriptions():
    subscriptions = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE,
        end_date__lte=timezone.now() + timedelta(hours=1)
    ).select_related('shop')
    for subscription in subscriptions:
        if subscription.end_date < timezone.now():
            subscription.status = Subscription.Status.EXPIRED
            subscription.save()
            logger.info(f"Updated subscription {subscription.id} for shop {subscription.shop.id} to EXPIRED")
            # Deactivate products associated with the shop
            products_updated = Product.objects.filter(
                shop=subscription.shop,
                is_active=True
            ).update(is_active=False)
            logger.info(f"Deactivated {products_updated} products for shop {subscription.shop.id}")
        else:
            # Ensure products are active if subscription is still valid
            products_updated = Product.objects.filter(
                shop=subscription.shop,
                is_active=False
            ).update(is_active=True)
            if products_updated:
                logger.info(f"Reactivated {products_updated} products for shop {subscription.shop.id}")