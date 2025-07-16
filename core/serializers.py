from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import University, Campus
from drf_spectacular.utils import extend_schema_field

class UniversitySerializer(serializers.ModelSerializer):
    """Simple serializer for University model - raw data only"""
    
    class Meta:
        model = University
        fields = [
            'id', 'name', 'short_name', 'radius_km', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CampusSerializer(serializers.ModelSerializer):
    """Simple serializer for Campus model - raw data with coordinates"""
    university_name = serializers.CharField(source='university.name', read_only=True)
    university_short_name = serializers.CharField(source='university.short_name', read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    
    class Meta:
        model = Campus
        fields = [
            'id', 'name', 'university', 'university_name', 'university_short_name',
            'latitude', 'longitude', 'address', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.CharField())
    def get_latitude(self, obj) -> str:
        """Get latitude from location PointField"""
        return obj.latitude
    
    @extend_schema_field(serializers.CharField())
    def get_longitude(self, obj) -> str:
        """Get longitude from location PointField"""
        return obj.longitude 