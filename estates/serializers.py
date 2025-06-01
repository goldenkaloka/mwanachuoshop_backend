from rest_framework import serializers
from django.urls import reverse
from .models import Property, PropertyImage, PropertyType
from users.models import NewUser, Profile
from dj_rest_auth.serializers import UserDetailsSerializer

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
    hls_playlist_url = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    # Explicitly define user-filled fields
    title = serializers.CharField(max_length=100, required=True)
    features = serializers.CharField(required=True)
    location = serializers.CharField(max_length=100, required=True)
    price = serializers.IntegerField(min_value=1, required=True)
    video = serializers.FileField(required=True, allow_null=False)  # Changed to required
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

    def get_thumbnail(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            request = self.context.get('request')
            return request.build_absolute_uri(primary_image.image.url) if request else primary_image.image.url
        return None

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