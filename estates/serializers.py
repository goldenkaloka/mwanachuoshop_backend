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
    images_upload = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        help_text="Upload multiple images at once."
    )

    title = serializers.CharField(max_length=100, required=True)
    features = serializers.CharField(required=True)
    location = serializers.CharField(max_length=100, required=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('1.00'), required=True)
    is_available = serializers.BooleanField(default=True)

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
            'created_at',
            'updated_at',
            'images',
            'images_upload',
        ]
        read_only_fields = [
            'slug',
            'created_at',
            'updated_at',
            'images',
        ]

    def create(self, validated_data):
        images_data = validated_data.pop('images_upload', [])
        property_instance = super().create(validated_data)
        for image in images_data:
            PropertyImage.objects.create(property=property_instance, image=image)
        return property_instance

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if not self.instance and Property.objects.filter(owner=request.user, title=data['title']).exists():
                raise serializers.ValidationError({"title": "A property with this title already exists for this user."})
        return data