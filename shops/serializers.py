from rest_framework import serializers
from .models import (
    SubscriptionPlan, 
    ShopSubscription, 
    Shop, 
    ShopMedia, 
    ShopService, 
    ShopPromotion
)
from django.contrib.auth import get_user_model

User = get_user_model()

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ('slug',)

class ShopSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(),
        source='plan',
        write_only=True
    )
    days_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = ShopSubscription
        fields = '__all__'
        read_only_fields = ('is_active', 'is_trial', 'created_at', 'days_remaining')

class ShopMediaSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = ShopMedia
        fields = '__all__'
        read_only_fields = ('uploaded_at',)

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_video_url(self, obj):
        if obj.video:
            return obj.video.url
        return None

    def validate(self, data):
        if not data.get('image') and not data.get('video'):
            raise serializers.ValidationError("Either image or video must be provided")
        return data

class ShopServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopService
        fields = '__all__'
        read_only_fields = ('shop',)

class ShopPromotionSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = ShopPromotion
        fields = '__all__'
        read_only_fields = ('shop', 'views')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class ShopSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    active_subscription = ShopSubscriptionSerializer(read_only=True)
    media_files = ShopMediaSerializer(many=True, read_only=True)
    services = ShopServiceSerializer(many=True, read_only=True)
    promotions = ShopPromotionSerializer(many=True, read_only=True)
    is_in_trial = serializers.BooleanField(source='in_trial_period', read_only=True)

    class Meta:
        model = Shop
        fields = '__all__'
        read_only_fields = ('slug', 'created_at', 'is_verified', 'is_active')

    def validate_slug(self, value):
        if Shop.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Shop with this slug already exists.")
        return value
    
