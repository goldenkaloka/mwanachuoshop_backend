from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Index
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from django_resized import ResizedImageField

User = settings.AUTH_USER_MODEL

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    is_trial = models.BooleanField(default=False)
    active = models.BooleanField(default=True, db_index=True)
    max_products = models.PositiveIntegerField(default=0)  # 0 means unlimited
    can_add_products = models.BooleanField(default=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # For pay-per-product
    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} (${self.price}/mo)"

    @classmethod
    def get_trial_plan(cls):
        return cls.objects.get(is_trial=True)

class ShopSubscription(models.Model):
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True, db_index=True)
    is_trial = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [Index(fields=['is_active', 'is_trial', 'end_date'])]
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
        if self.is_active:
            self.shop.subscriptions.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        return (self.end_date - timezone.now()).days if self.end_date else 0

class ShopQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            Q(subscriptions__end_date__gt=timezone.now()) & 
            Q(subscriptions__is_active=True) &
            Q(is_verified=True)
        )

    def needs_renewal(self):
        renewal_date = timezone.now() + timedelta(days=7)
        return self.filter(
            subscriptions__end_date__lte=renewal_date,
            subscriptions__end_date__gt=timezone.now()
        )

class ShopManager(models.Manager):
    def get_queryset(self):
        return ShopQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

class Shop(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops')
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    contact_whatsapp = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100)
    region = models.CharField(max_length=100, choices=[
        ('DAR', 'Dar es Salaam'), ('ARU', 'Arusha'), ('MBY', 'Mbeya')
    ])
    is_active = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    objects = ShopManager()

    class Meta:
        indexes = [
            Index(fields=['slug', 'is_active']),
            Index(fields=['region']),
            Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.region})"

    def add_subscription(self, duration_days, plan=None, is_trial=False):
        if not plan and not is_trial:
            raise ValueError("Either provide a plan or specify as trial")
            
        start_date = timezone.now()
        end_date = start_date + timedelta(days=duration_days)
        
        if is_trial:
            plan = SubscriptionPlan.get_trial_plan()
            
        return ShopSubscription.objects.create(
            shop=self,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            is_trial=is_trial
        )

    @property
    def active_subscription(self):
        return self.subscriptions.filter(
            is_active=True,
            end_date__gt=timezone.now()
        ).first()

    @property
    def in_trial_period(self):
        sub = self.active_subscription
        return sub and sub.is_trial

@receiver(post_save, sender=Shop)
def handle_new_shop(sender, instance, created, **kwargs):
    if created:
        instance.add_subscription(duration_days=30, is_trial=True)
        Shop.objects.filter(pk=instance.pk).update(is_verified=True)
        instance.owner.profile.has_shop = True
        instance.owner.profile.save()

class ShopMedia(models.Model):
    MEDIA_TYPES = [('logo', 'Logo'), ('banner', 'Banner'), ('gallery', 'Gallery')]
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='media_files')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    image = ResizedImageField(size=[1920, 1080], quality=85, upload_to='shop_media/', blank=True)
    video = models.FileField(upload_to='shop_media/', blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ShopService(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField()  # Minutes

    def clean(self):
        if not self.shop.active_subscription:
            raise ValidationError("Active subscription required to offer services")

class ShopPromotion(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='promotions')
    title = models.CharField(max_length=200)
    content = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    views = models.PositiveIntegerField(default=0)

    @property
    def is_active(self):
        now = timezone.now()
        if self.start_date and self.end_date:
            return self.start_date <= now <= self.end_date
        return False