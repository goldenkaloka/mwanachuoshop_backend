import os
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import post_save

class PropertyType(models.Model):
    """Managed by system admin"""
    name = models.CharField(max_length=50, unique=True)
    
    class Meta:
        verbose_name = "Property Type"
        verbose_name_plural = "Property Types"
        ordering = ['name']
    
    def __str__(self):
        return self.name

def validate_video_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    if ext not in valid_extensions:
        raise ValidationError('Unsupported video format. Supported formats: .mp4, .mov, .avi, .mkv, .webm')
    if value.size > 1024 * 1024 * 100:  # 100 MB limit
        raise ValidationError('File size exceeds the limit of 100 MB.')

class Property(models.Model):
    """Property model with integrated video support"""
    PENDING = 'Pending'
    PROCESSING = 'Processing'
    COMPLETED = 'Completed'
    FAILED = 'Failed'
    
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    property_type = models.ForeignKey(PropertyType, on_delete=models.PROTECT, related_name='properties')
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True, unique=True)
    features = models.TextField()
    location = models.CharField(max_length=100)
    price = models.PositiveIntegerField()  # TZS
    is_available = models.BooleanField(default=True)
    
    video_name = models.CharField(max_length=500, blank=True)
    video_description = models.TextField(blank=True)
    video = models.FileField(
        upload_to="properties/videos/original/",
        validators=[validate_video_file],
    )
    thumbnail = models.ImageField(
        upload_to="properties/videos/thumbnails/",
        null=True,
        blank=True
    )
    duration = models.FloatField(null=True, blank=True)
    hls_playlist = models.CharField(max_length=500, null=True, blank=True)
    video_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    is_video_processing = models.BooleanField(default=False)
    video_error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        ordering = ['-created_at']
        unique_together = ['owner', 'title']

    def __str__(self):
        return f"{self.title} - {self.location}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Property.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'created_at']
        verbose_name = "Property Image"
        verbose_name_plural = "Property Images"

    def save(self, *args, **kwargs):
        if self.is_primary:
            PropertyImage.objects.filter(
                property=self.property,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.property.title}"