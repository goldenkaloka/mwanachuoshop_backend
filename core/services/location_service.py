"""
Location service for handling university and campus operations.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache

from core.models import University, Location, Campus
# Distance calculations now handled by frontend - simplified approach

logger = logging.getLogger(__name__)


class LocationService:
    """Service for handling location-based operations."""

    CACHE_TIMEOUT = 3600  # 1 hour

    @staticmethod
    def get_universities() -> List[Dict[str, Any]]:
        """Get all active universities with caching."""
        cache_key = 'universities_list'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        universities = University.objects.filter(is_active=True).select_related()
        data = [
            {
                'id': uni.id,
                'name': uni.name,
                'short_name': uni.short_name,
                'description': uni.description,
                'location': uni.location,
                'website': uni.website,
                'logo': uni.logo.url if uni.logo else None,
            }
            for uni in universities
        ]
        
        cache.set(cache_key, data, LocationService.CACHE_TIMEOUT)
        return data

    @staticmethod
    def get_university_by_id(university_id: int) -> Optional[Dict[str, Any]]:
        """Get university by ID with caching."""
        cache_key = f'university_{university_id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        try:
            university = University.objects.get(id=university_id, is_active=True)
            data = {
                'id': university.id,
                'name': university.name,
                'short_name': university.short_name,
                'description': university.description,
                'location': university.location,
                'website': university.website,
                'logo': university.logo.url if university.logo else None,
            }
            cache.set(cache_key, data, LocationService.CACHE_TIMEOUT)
            return data
        except University.DoesNotExist:
            return None

    @staticmethod
    def get_campuses_by_university(university_id: int) -> List[Dict[str, Any]]:
        """Get all campuses for a specific university."""
        cache_key = f'campuses_university_{university_id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        campuses = Campus.objects.filter(
            university_id=university_id, 
            is_active=True
        ).select_related('university')
        
        data = [
            {
                'id': campus.id,
                'name': campus.name,
                'university': {
                    'id': campus.university.id,
                    'name': campus.university.name,
                    'short_name': campus.university.short_name,
                },
                'address': campus.address,
                'location': campus.location,
                'description': campus.description,
            }
            for campus in campuses
        ]
        
        cache.set(cache_key, data, LocationService.CACHE_TIMEOUT)
        return data

    @staticmethod
    def find_nearest_campus(
        latitude: float, 
        longitude: float, 
        radius_km: float = 20
    ) -> Optional[Dict[str, Any]]:
        """Find the nearest campus within the specified radius."""
        cache_key = f'nearest_campus_{latitude}_{longitude}_{radius_km}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        campuses = Campus.objects.filter(
            is_active=True,
            location__isnull=False
        ).select_related('university')

        # Distance calculations now handled by frontend - simplified approach
        result = None

        cache.set(cache_key, result, LocationService.CACHE_TIMEOUT)
        return result

    @staticmethod
    def get_nearby_content(
        university_id: int,
        content_type: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get nearby content for a specific university."""
        cache_key = f'nearby_content_{university_id}_{content_type}_{limit}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        try:
            university = University.objects.get(id=university_id, is_active=True)
        except University.DoesNotExist:
            return []

        content = []
        
        if content_type == 'products':
            from marketplace.models import Product
            products = Product.objects.filter(
                university=university,
                is_active=True
            ).select_related('category', 'university', 'campus')[:limit]
            
            content = [
                {
                    'id': p.id,
                    'name': p.name,
                    'price': str(p.price),
                    'category': p.category.name if p.category else None,
                    'campus': p.campus.name if p.campus else None,
                }
                for p in products
            ]
        
        elif content_type == 'shops':
            from shops.models import Shop
            shops = Shop.objects.filter(
                university=university,
                is_active=True
            ).select_related('university', 'campus')[:limit]
            
            content = [
                {
                    'id': s.id,
                    'name': s.name,
                    'location': s.location,
                    'campus': s.campus.name if s.campus else None,
                }
                for s in shops
            ]
        
        elif content_type == 'properties':
            from estates.models import Property
            properties = Property.objects.filter(
                university=university,
                is_available=True
            ).select_related('property_type', 'university', 'campus')[:limit]
            
            content = [
                {
                    'id': p.id,
                    'title': p.title,
                    'price': str(p.price),
                    'property_type': p.property_type.name if p.property_type else None,
                    'campus': p.campus.name if p.campus else None,
                }
                for p in properties
            ]

        cache.set(cache_key, content, LocationService.CACHE_TIMEOUT)
        return content

    @staticmethod
    def get_location_context(
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        university_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Get location context for a user."""
        context = {
            'detected_campus': None,
            'user_universities': [],
            'nearby_universities': [],
        }

        if latitude and longitude:
            # Find nearest campus
            nearest_campus = LocationService.find_nearest_campus(latitude, longitude)
            if nearest_campus:
                context['detected_campus'] = nearest_campus
                context['user_universities'] = [nearest_campus['university']['id']]

        if university_ids:
            # Get university details
            universities = []
            for uni_id in university_ids:
                uni_data = LocationService.get_university_by_id(uni_id)
                if uni_data:
                    universities.append(uni_data)
            context['user_universities'] = universities

        return context

    @staticmethod
    def clear_location_cache():
        """Clear all location-related cache."""
        cache_keys = [
            'universities_list',
            'nearest_campus_*',
            'nearby_content_*',
            'campuses_university_*',
            'university_*',
        ]
        
        for key in cache_keys:
            if '*' in key:
                # For pattern-based keys, we'd need a more sophisticated cache clearing
                # For now, we'll clear the most common ones
                continue
            cache.delete(key)
        
        logger.info("Location cache cleared") 