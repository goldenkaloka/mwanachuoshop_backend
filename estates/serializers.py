from rest_framework import serializers
from django.urls import reverse
from .models import Property, PropertyImage, PropertyType

class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ['id', 'name']

class PropertyImageSerializer(serializers.ModelSerializer):
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())

    class Meta:
        model = PropertyImage
        fields = ['id', 'property', 'image', 'is_primary', 'created_at']
        read_only_fields = ['created_at']

class PropertySerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    property_type = PropertyTypeSerializer(read_only=True)
    property_type_id = serializers.PrimaryKeyRelatedField(
        queryset=PropertyType.objects.all(),
        source='property_type',
        write_only=True
    )
    images = PropertyImageSerializer(many=True, read_only=True)
    hls_playlist_url = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id',
            'owner',
            'property_type',
            'property_type_id',
            'title',
            'slug',
            'features',
            'location',
            'price',
            'is_available',
            'video_name',
            'video_description',
            'video',
            'thumbnail',
            'duration',
            'hls_playlist',
            'hls_playlist_url',
            'video_status',
            'is_video_processing',
            'video_error_message',
            'created_at',
            'updated_at',
            'images',
        ]
        read_only_fields = [
            'slug',
            'created_at',
            'updated_at',
            'video_name',
            'video_description',
            'video',
            'thumbnail',
            'duration',
            'hls_playlist',
            'hls_playlist_url',
            'video_status',
            'is_video_processing',
            'video_error_message',
            'images',
        ]

    def get_hls_playlist_url(self, obj):
        if obj.video_status == Property.COMPLETED and obj.hls_playlist:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(reverse('property-playlist', args=[obj.id]))
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get('request') and self.context['request'].query_params.get('exclude_images', 'false') == 'true':
            representation.pop('images', None)
        return representation

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if Property.objects.filter(owner=request.user, title=data['title']).exists():
                raise serializers.ValidationError({"title": "A property with this title already exists for this user."})
        return data