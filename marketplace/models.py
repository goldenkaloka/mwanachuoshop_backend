from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
from django.utils import timezone
from django.utils.text import slugify

class Category(MPTTModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    parent = TreeForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    class Meta:
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='brands')
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name', 'category_id']),
            models.Index(fields=['category_id']),  # For filtering by category_id
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
    value = models.CharField(max_length=100, db_index=True)
    
    class Meta:
        unique_together = ('attribute', 'value')
        indexes = [
            models.Index(fields=['value']),
            models.Index(fields=['category_id']),  # For filtering by category_id
        ]
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    shop = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    attribute_values = models.ManyToManyField(AttributeValue, related_name='product_lines')
    is_active = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['brand_id']),
            models.Index(fields=['category_id']),
            models.Index(fields=['shop_id']),
            models.Index(fields=['owner_id']),
        ]
    
    def get_admin_url(self):
        from django.urls import reverse
        return reverse("admin:products_product_change", args=[self.id])
    
    def clean(self):
        if self.price <= 0:
            raise ValidationError("Price must be greater than zero.")
        if not self.name:
            raise ValidationError("Product name cannot be empty.")
        if not self.description:
            raise ValidationError("Product description cannot be empty.")
    
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
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)