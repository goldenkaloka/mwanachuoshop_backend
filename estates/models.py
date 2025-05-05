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

class Property(models.Model):
    """Property model with video support"""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    property_type = models.ForeignKey(PropertyType, on_delete=models.PROTECT, related_name='properties')
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True, unique=True)
    features = models.TextField()
    location = models.CharField(max_length=100)
    price = models.PositiveIntegerField()  # TZS
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']
        unique_together = ['owner', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.location}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
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
                property=self.property, is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.property.title}"

def validate_video_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    if ext not in valid_extensions:
        raise ValidationError('Unsupported video format. Supported formats: .mp4, .mov, .avi, .mkv, .webm')

class Video(models.Model):
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

    # Model fields
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='videos')
    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    video = models.FileField(upload_to="properties/videos/original/", validators=[validate_video_file])
    thumbnail = models.ImageField(upload_to="properties/videos/thumbnails/", null=True, blank=True)
    duration = models.FloatField(blank=True, null=True)
    hls_playlist = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    is_running = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Property Video"
        verbose_name_plural = "Property Videos"

    def __str__(self):
        return f"{self.name} - {self.property.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.property.title}-{self.name}")
        super().save(*args, **kwargs)
