from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db import transaction
from django.core.mail import mail_admins
from django.utils import timezone
from datetime import timedelta
from .models import UserOffer, Subscription, Shop
from payments.models import Payment
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_offer(sender, instance, created, **kwargs):
    """Create a UserOffer for new users with free product and estate quotas."""
    if created:
        try:
            with transaction.atomic():
                UserOffer.objects.create(
                    user=instance,
                    free_products_remaining=settings.USER_OFFER_DEFAULTS.get('free_products_remaining', 20),
                    free_estates_remaining=settings.USER_OFFER_DEFAULTS.get('free_estates_remaining', 5)
                )
                logger.info(f"Created UserOffer for user {instance.id} (email: {instance.email})")
        except Exception as e:
            error_msg = f"Failed to create UserOffer for user {instance.id} (email: {instance.email}): {str(e)}"
            logger.error(error_msg)
            mail_admins(
                subject="UserOffer Creation Failure",
                message=error_msg,
                fail_silently=True
            )

@receiver(post_save, sender=Shop)
def create_shop_trial_subscription(sender, instance, created, **kwargs):
    """Create a free trial subscription for new shops if no paid subscription exists."""
    if created:
        try:
            with transaction.atomic():
                # Check if a paid subscription payment exists
                has_paid_subscription = Payment.objects.filter(
                    user=instance.user,
                    content_type=ContentType.objects.get_for_model(Subscription),
                    object_id__isnull=True,  # Null until subscription is created
                    payment_type=Payment.PaymentType.SUBSCRIPTION,
                    status=Payment.PaymentStatus.COMPLETED
                ).exists()
                if has_paid_subscription:
                    logger.info(f"Skipping trial subscription for shop {instance.id} due to existing paid subscription")
                    return

                trial_days = getattr(settings, 'SHOP_TRIAL_DAYS', 7)
                trial_end = timezone.now() + timedelta(days=trial_days)
                if settings.DEBUG and hasattr(settings, 'SHOP_TRIAL_MINUTES'):
                    trial_end = timezone.now() + timedelta(minutes=settings.SHOP_TRIAL_MINUTES)

                subscription, sub_created = Subscription.objects.get_or_create(
                    shop=instance,
                    defaults={
                        'user': instance.user,
                        'status': Subscription.Status.ACTIVE,
                        'start_date': timezone.now(),
                        'end_date': trial_end,
                        'is_trial': True
                    }
                )
                if sub_created:
                    instance.is_active = True
                    instance.save(update_fields=['is_active'])
                    logger.info(f"Created trial subscription for shop {instance.id} (user: {instance.user.email}) with end_date {trial_end}")
                else:
                    logger.warning(f"Subscription already exists for shop {instance.id}, end_date {subscription.end_date}")
        except Exception as e:
            error_msg = f"Failed to create trial subscription for shop {instance.id} (user: {instance.user.email}): {str(e)}"
            logger.error(error_msg)
            mail_admins(
                subject="Shop Trial Subscription Creation Failure",
                message=error_msg,
                fail_silently=True
            )