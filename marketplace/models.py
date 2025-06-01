from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from django.utils import timezone
from django.utils.text import slugify

class Category(MPTTModel):
    name = models.CharField(max_length=100, unique=True)  # Removed db_index=True
    parent = TreeForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    class Meta:
        verbose_name_plural = "Categories"
        indexes = []  # Removed redundant index on 'name'
    
    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='brands')
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['category_id']),  # Removed composite index
        ]
    
    def __str__(self):
        return self.name

class Attribute(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name

class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)  # Removed db_index=True
    
    class Meta:
        unique_together = ('attribute', 'value')
        indexes = [
            models.Index(fields=['value']),
            models.Index(fields=['category_id']),
        ]
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

class Product(models.Model):
    class Condition(models.TextChoices):
        NEW = 'new', 'New'
        USED = 'used', 'Used'
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    shop = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    condition = models.CharField(max_length=100, choices=Condition.choices, default=Condition.USED)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    attribute_values = models.ManyToManyField(AttributeValue, related_name='product_lines')
    is_active = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['brand_id']),
            models.Index(fields=['category_id']),
            models.Index(fields=['shop_id']),
            models.Index(fields=['owner_id']),
            models.Index(fields=['created_at'])
        ]

    
    def clean(self):
        if self.price <= 0:
            raise ValidationError("Price must be greater than zero.")
        if not self.name:
            raise ValidationError("Product name cannot be empty.")
        if not self.description:
            raise ValidationError("Product description cannot be empty.")
        if self.shop and self.shop.owner != self.owner:
            raise ValidationError("Shop must belong to the product owner.")
        if self.pk:  # Only validate attribute_values for saved instances
            for attr_value in self.attribute_values.all():
                if attr_value.category != self.category:
                    raise ValidationError(f"Attribute value {attr_value} does not belong to category {self.category}.")
                
                
    def check_shop_subscription(self):
        """Check if the associated shop has an active subscription."""
        if self.shop:
            return self.shop.is_subscription_active()
        return True  # Products without a shop are not affected by subscriptions
    

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.product}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)
        # Ensure at least one image is primary if images exist
        if not self.product.images.filter(is_primary=True).exists() and self.product.images.exists():
            first_image = self.product.images.first()
            first_image.is_primary = True
            first_image.save()

class WhatsAppClick(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='whatsapp_clicks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['product', 'clicked_at']),
            models.Index(fields=['clicked_at']),
        ]

    def __str__(self):
        return f"Click on {self.product.name} at {self.clicked_at}"