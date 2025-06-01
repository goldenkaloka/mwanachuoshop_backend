# shops/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import UserOffer, Subscription, Shop
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_offer(sender, instance, created, **kwargs):
    if created:
        try:
            UserOffer.objects.create(
                user=instance,
                free_products_remaining=20,
                free_estates_remaining=5
             
            )
            logger.info(f"Created UserOffer for user {instance.id}")
        except Exception as e:
            logger.error(f"Failed to create UserOffer for user {instance.id}: {str(e)}")

@receiver(post_save, sender=Shop)
def create_shop_subscription(sender, instance, created, **kwargs):
    if created:
        try:
            try:
                offer = instance.user.offer
            except UserOffer.DoesNotExist:
                offer = UserOffer.objects.create(
                    user=instance.user,
                    free_products_remaining=20,
                    free_estates_remaining=5
                )
                logger.info(f"Created UserOffer for user {instance.user.id} for shop {instance.id}")
            
            # Set shop_trial_end_date when shop is created
            trial_end = timezone.now() + timedelta(minutes=3)
            offer.shop_trial_end_date = trial_end
            offer.save()
            logger.info(f"Set shop_trial_end_date to {trial_end} for user {instance.user.id}")

            subscription, created = Subscription.objects.get_or_create(
                shop=instance,
                defaults={
                    'user': instance.user,
                    'end_date': trial_end,
                    'is_trial': True
                }
            )
            if created:
                logger.info(f"Created Subscription for shop {instance.id} with end_date {subscription.end_date}")
            else:
                logger.info(f"Subscription already exists for shop {instance.id}, end_date {subscription.end_date}")
        except Exception as e:
            logger.error(f"Failed to create Subscription for shop {instance.id}: {str(e)}")