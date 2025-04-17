from datetime import timedelta, timezone
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField

from shops.models import Shop, ShopSubscription, SubscriptionPlan



class CustomAccountManager(BaseUserManager):
    def create_superuser(self, email, username, firstname, password, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)
        
        if other_fields.get('is_staff') is not True:
            raise ValueError('Superuser must be assigned to is_staff=True')
        
        if other_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must be assigned to is_superuser=True')
            
        return self.create_user(email, username, firstname, password, **other_fields)
        
    def create_user(self, email, username, firstname, password, **other_fields):
        if not email:
            raise ValueError('You must provide an email address')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            firstname=firstname,
            **other_fields
        )
        user.set_password(password)
        user.save()
        return user


class NewUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(max_length=150, unique=True)
    firstname = models.CharField(max_length=150, blank=True)
    phonenumber = PhoneNumberField(region='TZ', unique=True)
    start_date = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Marketplace fields
    free_product_limit = models.PositiveIntegerField(default=20)
    products_posted = models.PositiveIntegerField(default=0)
    
    # Shop fields
    has_shop = models.BooleanField(default=False)
    
    objects = CustomAccountManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'firstname', 'phonenumber']
    
    @property
    def can_post_free_product(self):
        """Check if user can post another free product"""
        return self.products_posted < self.free_product_limit
    
    def record_product_post(self):
        """Thread-safe product count increment"""
        from django.db.models import F
        NewUser.objects.filter(pk=self.pk).update(products_posted=F('products_posted') + 1)
        self.refresh_from_db()
    
    @property
    def remaining_free_products(self):
        return max(0, self.free_product_limit - self.products_posted)
    
    def can_post_product(self, shop=None):
        """
        Check if user can post a product, either through shop or individually
        """
        if shop:
            if not shop.active_subscription:
                return False
            if shop.active_subscription.plan.max_products == 0:
                return True
            return shop.products.filter(is_active=True).count() < shop.active_subscription.plan.max_products
        else:
            return self.can_post_free_product
    
    def get_full_name(self):
        return self.firstname
    
    def get_short_name(self):
        return self.firstname
    
    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(
        NewUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    image = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )
    whatsapp = PhoneNumberField(
        region='TZ',
        blank=True,
        null=True
    )
    instagram = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    tiktok = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    whatsapp_verified = models.BooleanField(default=False)
    whatsapp_verification_code = models.CharField(max_length=6, null=True, blank=True)
    whatsapp_last_verified = models.DateTimeField(null=True, blank=True)
    whatsapp_verification_attempts = models.PositiveIntegerField(default=0)

    def generate_verification_code(self):
        import random
        self.whatsapp_verification_code = str(random.randint(100000, 999999))
        self.save()
        return self.whatsapp_verification_code
    
    def verify_whatsapp(self, code):
        if self.whatsapp_verification_code == code:
            self.whatsapp_verified = True
            self.whatsapp_verification_code = None
            self.whatsapp_last_verified = timezone.now()
            self.save()
            return True
        self.whatsapp_verification_attempts += 1
        self.save()
        return False
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    


class BasePayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('azampay', 'AzamPay'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
    ]
    
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='azampay')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def mark_as_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

class SubscriptionPayment(BasePayment):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='subscription_payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    subscription = models.ForeignKey(ShopSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Subscription Payment #{self.id} - {self.amount} ({self.status})"

class ProductPayment(BasePayment):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('marketplace.Product', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Product Payment #{self.id} - {self.amount} ({self.status})"