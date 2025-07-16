from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import logging
from django.contrib.gis.db import models as gis_models
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class University(models.Model):
    """University model to organize location-based content"""
    name = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=50, unique=True)
    location = gis_models.PointField(geography=True, null=True, blank=True)
    radius_km = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.00,
        validators=[MinValueValidator(0.1), MaxValueValidator(50.0)],
        help_text="Radius in kilometers to consider as 'near' this university"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['short_name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

class Campus(models.Model):
    name = models.CharField(max_length=255)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='campuses')
    location = gis_models.PointField(geography=True, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'university')
        ordering = ['university', 'name']
        indexes = [
            models.Index(fields=['university']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.university.short_name})" 

    @property
    def latitude(self):
        """Get latitude from location PointField"""
        if self.location:
            return self.location.y
        return None
    
    @property
    def longitude(self):
        """Get longitude from location PointField"""
        if self.location:
            return self.location.x
        return None 

User = get_user_model()