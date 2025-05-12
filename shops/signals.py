from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import PermissionDenied
from .models import UserOffer, Subscription, Shop
from marketplace.models import Product
from estates.models import Property
from payments.models import PaymentService, Payment

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_offer(sender, instance, created, **kwargs):
    if created:
        UserOffer.objects.create(
            user=instance,
            shop_trial_end_date=timezone.now() + timedelta(days=30)
        )

@receiver(post_save, sender=Shop)
def create_shop_subscription(sender, instance, created, **kwargs):
    if created:
        offer = instance.user.offer
        Subscription.objects.create(
            user=instance.user,
            shop=instance,
            end_date=offer.shop_trial_end_date,
            is_trial=True
        )


@receiver(pre_save, sender=Property)
def check_estate_creation_permissions(sender, instance, **kwargs):
    user = instance.owner
    shop = getattr(user, 'shop', None)
    
    if shop and shop.is_subscription_active():
        return
    
    offer = getattr(user, 'offer', None)
    if offer and offer.consume_free_estate():
        return
    
    payment_service = PaymentService.objects.get(name=PaymentService.ServiceName.ESTATE_CREATION)
    has_paid = Payment.objects.filter(
        user=user,
        service=payment_service,
        status=Payment.PaymentStatus.COMPLETED
    ).exists()
    
    if not has_paid:
        raise PermissionDenied("You must purchase an estate creation service to post more properties.")