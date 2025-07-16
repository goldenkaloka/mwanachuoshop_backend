from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
from django.db import transaction
import logging
from django.contrib.gis.db import models as gis_models

from payments.models import Payment
from core.models import University, Campus

logger = logging.getLogger(__name__)

class PropertyType(models.Model):
    """Managed by system admin"""
    name = models.CharField(max_length=50, unique=True)
    
    class Meta:
        verbose_name = "Property Type"
        verbose_name_plural = "Property Types"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Property(models.Model):
    """Property model with image support only (no video)"""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    property_type = models.ForeignKey(PropertyType, on_delete=models.PROTECT, related_name='properties')
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True, unique=True)
    features = models.TextField()
    location = models.CharField(max_length=100, help_text="Geographical location of the property.", default='dar es salaam')
    price = models.DecimalField(max_digits=15, decimal_places=2, help_text="Price of the property in TZS.")
    is_available = models.BooleanField(default=False, help_text="Indicates if the property is active and visible to users.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Change campus to ManyToManyField
    campus = models.ManyToManyField(Campus, related_name='properties', blank=True)

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        ordering = ['-created_at']
        unique_together = ['owner', 'title']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['is_available']),
            models.Index(fields=['property_type']),
            models.Index(fields=['price']),
            models.Index(fields=['slug']),
            models.Index(fields=['location']),
            models.Index(fields=['is_available', 'location']),
        ]

    def __str__(self):
        return f"{self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Property.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        if not self.title:
            raise ValidationError("Property title cannot be empty.")
        if not self.features:
            raise ValidationError("Property features cannot be empty.")
        if self.price <= 0:
            raise ValidationError("Property price must be greater than zero.")

    def activate_property(self):
        """Activate the property by deducting payment from the user's wallet."""
        if self.is_available:
            logger.info(f"Property {self.id} already available for user {self.owner.username}.")
            return

        with transaction.atomic():
            payment_amount = (Decimal(self.price) * Decimal('0.01')).quantize(Decimal('0.01'))
            logger.info(f"Calculated payment amount: {payment_amount} TZS for property {self.id}")
            payment = Payment.objects.create(
                user=self.owner,
                amount=payment_amount,
                status=Payment.PaymentStatus.PENDING,
                content_type=ContentType.objects.get_for_model(Property),
                object_id=self.id,
                payment_type=Payment.PaymentType.ESTATE,
                service=None
            )
            logger.info(f"Created payment {payment.id} for property {self.id}, amount: {payment_amount} TZS")
            try:
                payment.process_payment()
                self.is_available = True
                self.save(update_fields=['is_available', 'updated_at'])
                logger.info(f"Property {self.id} activated via wallet for user {self.owner.username}, amount: {payment_amount} TZS. Status: {payment.status}")
            except ValidationError as e:
                logger.error(f"Property activation failed for property {self.id}: {str(e)}")
                payment.status = Payment.PaymentStatus.FAILED
                payment.save()
                raise

class PropertyImage(models.Model):
    """Property image model"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_images')
    image = models.ImageField(upload_to='property_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Property Image"
        verbose_name_plural = "Property Images"
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"Image for {self.property.title}"

    def save(self, *args, **kwargs):
        # If this image is being set as primary, unset all other primary images for this property
        if self.is_primary:
            PropertyImage.objects.filter(property=self.property, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)