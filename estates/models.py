from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

class PropertyType(models.Model):
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=30)
    
    def __str__(self):
        return self.name

class ListingPayment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    listing = models.OneToOneField('PropertyListing', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.get_status_display()}"

class PropertyListing(models.Model):
    LISTING_TYPES = [
        ('rent', 'For Rent'),
        ('sale', 'For Sale'),
        ('shared', 'Shared Space')
    ]
    
    LISTING_STATUS = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('sold', 'Sold/Rented')
    ]
    
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_listings')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES)
    property_type = models.ForeignKey(PropertyType, on_delete=models.PROTECT)
    region = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    street_address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=LISTING_STATUS, default='draft')
    is_featured = models.BooleanField(default=False)
    featured_expiry = models.DateTimeField(null=True, blank=True)
    virtual_tour = models.URLField(blank=True)
    whatsapp_contact = models.CharField(max_length=15)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_verify_listing', 'Can verify property listings'),
        ]

    def clean(self):
        # Ensure featured listings require payment
        if self.is_featured and not hasattr(self, 'payment'):
            raise ValidationError("Payment is required for featured listings")

    def save(self, *args, **kwargs):
        # Set expiry for featured listings (30 days from creation)
        if self.is_featured and not self.featured_expiry:
            self.featured_expiry = timezone.now() + timedelta(days=30)
        
        # Update status based on payment
        if hasattr(self, 'payment'):
            if self.payment.status == 'completed' and self.status == 'pending':
                self.status = 'active'
            elif self.payment.status == 'failed' and self.status != 'draft':
                self.status = 'pending'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.get_listing_type_display()}"

class PropertyMedia(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('floorplan', 'Floor Plan')
    ]
    
    property = models.ForeignKey(PropertyListing, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='realestate/')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    thumbnail = ProcessedImageField(
        upload_to='property_thumbnails/',
        processors=[ResizeToFill(400, 225)],
        format='JPEG',
        options={'quality': 80},
        blank=True
    )
    
    class Meta:
        ordering = ['-is_primary', 'uploaded_at']
        verbose_name_plural = 'Property media'

    def save(self, *args, **kwargs):
        # Ensure only one primary image per property
        if self.is_primary:
            PropertyMedia.objects.filter(property=self.property).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_media_type_display()} for {self.property.title}"

class ListingPrice(models.Model):
    """Model to configure pricing for different listing types"""
    listing_type = models.CharField(max_length=20, choices=PropertyListing.LISTING_TYPES, unique=True)
    standard_price = models.DecimalField(max_digits=12, decimal_places=2)
    featured_price = models.DecimalField(max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)  # How long listing stays active
    
    def __str__(self):
        return f"Pricing for {self.get_listing_type_display()}"