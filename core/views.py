from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.conf import settings
import json
import logging
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat, Coalesce
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Avg, Count
from django.utils import timezone
from django.db import connection
from django.db import models
from .models import University, Campus
from .serializers import (
    UniversitySerializer, CampusSerializer
)
from django.contrib.gis.db.models.functions import Distance
# Remove any lingering references to LocationViewSet or Location

logger = logging.getLogger(__name__)



class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for University model - read-only for regular users"""
    queryset = University.objects.filter(is_active=True)
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Optimize queries with select_related and prefetch_related"""
        return super().get_queryset().prefetch_related('campuses')
    
    def list(self, request, *args, **kwargs):
        """Simple list endpoint - location logic handled by frontend"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def campuses(self, request, pk=None):
        """Get all campuses for a specific university"""
        university = self.get_object()
        campuses = Campus.objects.filter(university=university, is_active=True)
        serializer = CampusSerializer(campuses, many=True)
        return Response(serializer.data)
    
    # Content filtering now handled by app-specific endpoints with parameters

class CampusViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Campus model - read-only for regular users"""
    queryset = Campus.objects.filter(is_active=True)
    serializer_class = CampusSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Filter campuses by university if specified"""
        queryset = super().get_queryset()
        university_id = self.request.query_params.get('university_id')
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        return queryset.select_related('university')  # Optimize with select_related

    @action(detail=False, methods=['get'])
    def all(self, request):
        """
        Get all campuses with coordinates - frontend handles distance calculations
        """
        campuses = Campus.objects.filter(
            is_active=True
        ).select_related('university')

        campuses_data = []
        for campus in campuses:
            campus_data = CampusSerializer(campus).data
            campus_data['university'] = UniversitySerializer(campus.university).data
            # Include coordinates for frontend distance calculation
            campus_data['latitude'] = campus.latitude
            campus_data['longitude'] = campus.longitude
            campuses_data.append(campus_data)

        return Response({
            'campuses': campuses_data
        })

    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby(self, request):
        """
        Get campuses within a given radius (km) of provided lat/lng.
        Example: /api/campuses/nearby/?lat=-6.8&lng=39.2&radius=20
        """
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import D
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response({'error': 'lat and lng are required and must be valid numbers.'}, status=400)
        radius = float(request.query_params.get('radius', 20))
        user_location = Point(lng, lat)  # Note: Point(x, y) = (lng, lat)
        qs = Campus.objects.filter(
            is_active=True,
            location__isnull=False,
            location__distance_lte=(user_location, D(km=radius))
        ).annotate(
            distance=Distance('location', user_location)
        ).order_by('distance').select_related('university')
        data = []
        for campus in qs:
            campus_data = CampusSerializer(campus).data
            campus_data['distance_km'] = round(campus.distance.km, 2) if hasattr(campus, 'distance') else None
            campus_data['university'] = UniversitySerializer(campus.university).data
            data.append(campus_data)
        return Response({'campuses': data})

# Location context and suggestions now handled by frontend

# Products filtering now handled by marketplace app with university_id parameter

# Shops filtering now handled by shops app with university_id parameter
