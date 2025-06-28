from datetime import datetime, timedelta
from rest_framework import serializers
from django.urls import reverse
from decimal import Decimal
from .models import Property, PropertyImage, PropertyType
from users.models import NewUser, Profile
from dj_rest_auth.serializers import UserDetailsSerializer
import os
from cloudflare import Cloudflare
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

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

class CustomUserDetailsSerializer(UserDetailsSerializer):
    profile_id = serializers.IntegerField(source='profile.id', read_only=True)
    whatsapp = serializers.CharField(source='profile.whatsapp', read_only=True, allow_null=True)
    profile_image = serializers.ImageField(source='profile.image', read_only=True, allow_null=True)

    class Meta(UserDetailsSerializer.Meta):
        model = NewUser
        fields = UserDetailsSerializer.Meta.fields + (
            'phonenumber',
            'profile_id',
            'whatsapp',
            'profile_image',
        )
        read_only_fields = ('email', 'username', 'phonenumber', 'profile_id', 'whatsapp', 'profile_image')

class ProfileSerializer(serializers.ModelSerializer):
    user = CustomUserDetailsSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ('user',)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class PropertySerializer(serializers.ModelSerializer):
    owner = CustomUserDetailsSerializer(read_only=True, default=serializers.CurrentUserDefault())
    property_type = PropertyTypeSerializer(read_only=True)
    property_type_id = serializers.PrimaryKeyRelatedField(
        queryset=PropertyType.objects.all(),
        source='property_type',
        write_only=True
    )
    images = PropertyImageSerializer(many=True, read_only=True)
    video_uid = serializers.SerializerMethodField()
    video_token = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()  # Retained for backward compatibility
    thumbnail = serializers.SerializerMethodField()
    video = serializers.FileField(write_only=True, required=True, allow_null=False)
    video_status = serializers.SerializerMethodField()

    title = serializers.CharField(max_length=100, required=True)
    features = serializers.CharField(required=True)
    location = serializers.CharField(max_length=100, required=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('1.00'), required=True)
    is_available = serializers.BooleanField(default=True)
    video_name = serializers.CharField(max_length=500, required=False, allow_blank=True)
    video_description = serializers.CharField(required=False, allow_blank=True)

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
            'video_uid',
            'video_token',
            'video_url',
            'thumbnail',
            'duration',
            'video_status',
            'created_at',
            'updated_at',
            'images',
        ]
        read_only_fields = [
            'slug',
            'created_at',
            'updated_at',
            'video_uid',
            'video_token',
            'video_url',
            'thumbnail',
            'duration',
            'video_status',
            'images',
        ]

    def validate_video(self, value):
        ext = os.path.splitext(value.name)[1].lower()
        valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        if ext not in valid_extensions:
            raise serializers.ValidationError('Unsupported video format. Supported formats: MP4, MOV, AVI, MKV, WEBM.')
        if value.size > 1024 * 1024 * 100:  # 100 MB limit
            raise serializers.ValidationError('Video file size exceeds 100 MB.')
        return value

    def get_video_uid(self, obj):
        """Returns the Cloudflare Stream video UID."""
        return obj.stream_video_id if obj.stream_video_id else None

    def get_video_token(self, obj):
        """Returns a signed token for the video if signed URLs are enabled."""
        if obj.stream_video_id and getattr(settings, 'CLOUDFLARE_STREAM_SIGNED_URLS', False):
            cf = Cloudflare(api_token=settings.CLOUDFLARE_STREAM_API_TOKEN)
            try:
                token = cf.stream.token.create(
                    account_id=settings.CLOUDFLARE_ACCOUNT_ID,
                    video_id=obj.stream_video_id,
                    expiry=int((datetime.now() + timedelta(days=1)).timestamp())
                ).url
                return token
            except Exception as e:
                logger.error(f"Failed to generate signed token for video {obj.stream_video_id}: {str(e)}")
                return None
        return None

    def get_video_url(self, obj):
        """Returns the HLS playlist URL (retained for backward compatibility)."""
        if obj.stream_video_id:
            if getattr(settings, 'CLOUDFLARE_STREAM_SIGNED_URLS', False):
                return self.get_video_token(obj)
            return f"https://customer-{obj.stream_video_id}.cloudflarestream.com/manifest/video.m3u8"
        return None

    def get_thumbnail(self, obj):
        """Returns the thumbnail URL from Cloudflare Stream or primary image."""
        if obj.thumbnail_url:
            return obj.thumbnail_url
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            request = self.context.get('request')
            return request.build_absolute_uri(primary_image.image.url) if request else primary_image.image.url
        return None

    def get_video_status(self, obj):
        """Returns the video processing status."""
        if not obj.stream_video_id:
            return None
        cf = Cloudflare(api_token=settings.CLOUDFLARE_STREAM_API_TOKEN)
        try:
            video = cf.stream.get(identifier=obj.stream_video_id, account_id=settings.CLOUDFLARE_ACCOUNT_ID)
            return video.status.state  # 'pending', 'processing', 'ready', 'failed'
        except Exception as e:
            logger.error(f"Failed to fetch video status for {obj.stream_video_id}: {str(e)}")
            return 'failed'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get('request') and self.context['request'].query_params.get('exclude_images', 'false') == 'true':
            representation.pop('images', None)
        return representation

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if not self.instance and Property.objects.filter(owner=request.user, title=data['title']).exists():
                raise serializers.ValidationError({"title": "A property with this title already exists for this user."})
        return data