from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta
from phonenumber_field.modelfields import PhoneNumberField
from django.db import transaction
import logging
from marketplace.models import Product

logger = logging.getLogger(__name__)

class Shop(models.Model):
    image = models.ImageField(upload_to='shop-profile/')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shop')
    name = models.CharField(max_length=255)
    phone = PhoneNumberField(region='TZ')
    location = models.CharField(max_length=255)
    description = models.TextField()
    operating_hours = models.JSONField(default=dict)
    social_media = models.JSONField(blank=True, null=True)
    university_partner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_active']),
        ]

    def is_subscription_active(self):
        subscription = getattr(self, 'subscription', None)
        return subscription and subscription.is_active()

    def __str__(self):
        return self.name

class ShopMedia(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='media')
    image = models.ImageField(upload_to='shop_images/', blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_primary:
            ShopMedia.objects.filter(shop=self.shop, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

class Promotion(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='promotions')
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        if self.start_date is None or self.end_date is None:
            return False
        return (self.start_date <= timezone.now() <= self.end_date and
                self.shop.is_subscription_active())

    def __str__(self):
        return self.title

class Event(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_free = models.BooleanField(default=True)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        if self.start_time is None or self.end_time is None:
            return False
        return (self.start_time <= timezone.now() <= self.end_time and
                self.shop.is_subscription_active())

    def __str__(self):
        return self.title

class Services(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DurationField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_available(self):
        return self.shop.is_subscription_active()

    def __str__(self):
        return self.name

class UserOffer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offer')
    free_products_remaining = models.PositiveIntegerField(default=0)
    free_estates_remaining = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def consume_free_product(self):
        with transaction.atomic():
            if self.free_products_remaining > 0:
                self.free_products_remaining -= 1
                self.save()
                return True
            return False

    def consume_free_estate(self):
        with transaction.atomic():
            if self.free_estates_remaining > 0:
                self.free_estates_remaining -= 1
                self.save()
                return True
            return False

    def __str__(self):
        return f"Offer for {self.user.username}"

class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        CANCELED = 'canceled', 'Canceled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    shop = models.OneToOneField('Shop', on_delete=models.CASCADE, related_name='subscription')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_trial = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'end_date']),
            models.Index(fields=['shop']),
        ]

    def is_active(self):
        if self.status == self.Status.ACTIVE and self.end_date < timezone.now():
            with transaction.atomic():
                self.status = self.Status.EXPIRED
                self.save()
                self.shop.is_active = False
                self.shop.save(update_fields=['is_active'])
                products_updated = Product.objects.filter(
                    shop=self.shop,
                    is_active=True
                ).update(is_active=False)
                logger.info(f"Deactivated {products_updated} products and shop {self.shop.id} due to expired subscription")
        return self.status == self.Status.ACTIVE and self.end_date > timezone.now()

    def extend_subscription(self, months=1):
        with transaction.atomic():
            if self.end_date < timezone.now():
                self.end_date = timezone.now()
            self.end_date += timedelta(days=30 * months)
            self.is_trial = False
            self.status = self.Status.ACTIVE
            self.shop.is_active = True
            self.shop.save(update_fields=['is_active'])
            self.save()
            products_updated = Product.objects.filter(
                shop=self.shop,
                is_active=False
            ).update(is_active=True)
            logger.info(f"Reactivated {products_updated} products and shop {self.shop.id} due to subscription extension")

    def __str__(self):
        return f"Subscription for {self.shop.name} ({self.user.username})"