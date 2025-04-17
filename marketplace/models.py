from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
from marketplace.utils.payment import PaymentProcessor
from shops.models import Shop
from django.utils import timezone
from django.utils.text import slugify

class Category(MPTTModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True)
    parent = TreeForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='category_images/', null=True, blank=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    class Meta:
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='brand_logos/', null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name

class Attribute(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name

class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=100)
    
    class Meta:
        unique_together = ('attribute', 'value')
        indexes = [
            models.Index(fields=['value']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

class ProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def create_product(self, owner, **kwargs):
        shop = kwargs.pop('shop', None)
        requires_payment = not kwargs.pop('is_free', False)
        
        if shop:
            if not shop.is_active:
                raise ValidationError("Shop is not active")
            if not shop.has_active_subscription():
                raise ValidationError("Shop doesn't have an active subscription")
            
            product = self.model(owner=owner, shop=shop, **kwargs)
            product.save()
            return product
        else:
            if requires_payment:
                product = self.model(owner=owner, is_active=False, **kwargs)
                product.save()
                payment, _ = PaymentProcessor.process_product_payment(owner, product)
                
                if payment.status != 'completed':
                    product.delete()
                    raise ValidationError("Payment initiation failed")
                
                return product
            else:
                if owner.can_post_free_product():
                    product = self.model(owner=owner, is_free=True, **kwargs)
                    product.save()
                    owner.record_product_post()
                    return product
                raise ValidationError("Free product limit reached")
            
    def search_and_filter(self, search_query=None, category_ids=None, brand_ids=None, min_price=None, max_price=None):
        queryset = self.get_queryset()
        
        # Search by product name or description
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Filter by categories
        if category_ids:
            queryset = queryset.filter(category_id__in=category_ids)
        
        # Filter by brands
        if brand_ids:
            queryset = queryset.filter(brand_id__in=brand_ids)
        
        # Price range filtering
        if min_price or max_price:
            price_filter = Q()
            if min_price:
                price_filter &= Q(product_lines__price__gte=min_price)
            if max_price:
                price_filter &= Q(product_lines__price__lte=max_price)
            queryset = queryset.filter(price_filter).distinct()
        
        return queryset

class Product(models.Model):
    PRODUCT_TYPES = (
        ('physical', 'Physical'),
        ('digital', 'Digital'),
        ('service', 'Service'),
    )
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ProductManager()
    all_objects = models.Manager()  # Includes inactive products
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['brand', 'category']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.shop and not self.shop.is_active:
            raise ValidationError("Cannot assign product to inactive shop")
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            if Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)

class ProductLine(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_lines')
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    attribute_values = models.ManyToManyField(AttributeValue, related_name='product_lines')
    
    class Meta:
        ordering = ['price']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['price']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.sku}"
    
    @property
    def current_price(self):
        return self.sale_price if self.sale_price else self.price
    
    def is_in_stock(self):
        return self.stock_qty > 0

class ProductImage(models.Model):
    product_line = models.ForeignKey(ProductLine, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.product_line}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
        
            ProductImage.objects.filter(product_line=self.product_line, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)