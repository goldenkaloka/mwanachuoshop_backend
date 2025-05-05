from rest_framework import serializers
from .models import Property, PropertyType, PropertyImage, Video
from django.urls import reverse

class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ['id', 'name']
        read_only_fields = ['id']

class PropertyImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'image_url', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at', 'image_url']
    
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

class VideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    hls_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id', 'name', 'slug', 'description', 'video', 'video_url',
            'thumbnail', 'thumbnail_url', 'duration', 'hls_playlist', 'hls_url',
            'status', 'status_display', 'is_running', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'video_url', 'thumbnail_url', 'hls_url',
            'duration', 'status', 'status_display', 'is_running',
            'error_message', 'created_at', 'updated_at'
        ]
    
    def get_video_url(self, obj):
        return obj.video_url
    
    def get_hls_url(self, obj):
        return obj.hls_url
    
    def get_thumbnail_url(self, obj):
        return obj.thumbnail_url

class PropertySerializer(serializers.ModelSerializer):
    property_type = PropertyTypeSerializer(read_only=True)
    property_type_id = serializers.PrimaryKeyRelatedField(
        queryset=PropertyType.objects.all(),
        source='property_type',
        write_only=True
    )
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    images = PropertyImageSerializer(many=True, read_only=True)
    videos = VideoSerializer(many=True, read_only=True)
    image_count = serializers.SerializerMethodField()
    video_count = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'owner', 'property_type_id', 'property_type', 'title', 'slug',
            'features', 'location', 'price', 'is_available', 'created_at',
            'updated_at', 'images', 'videos', 'image_count', 'video_count',
            'detail_url'
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'updated_at', 'images', 'videos',
            'image_count', 'video_count', 'detail_url'
        ]
    
    def get_image_count(self, obj):
        return obj.images.count()
    
    def get_video_count(self, obj):
        return obj.videos.count()
    
    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(reverse('property-detail', kwargs={'pk': obj.pk}))
        return None
    
    def validate_title(self, value):
        if Property.objects.filter(owner=self.context['request'].user, title=value).exists():
            raise serializers.ValidationError("You already have a property with this title.")
        return value