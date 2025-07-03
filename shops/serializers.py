from rest_framework import serializers
from .models import Shop, ShopMedia, Promotion, Event, Services, Subscription, UserOffer
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

class SubscriptionSerializer(serializers.ModelSerializer):
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = ['id', 'status', 'start_date', 'end_date', 'is_trial', 'created_at', 'is_active']
        read_only_fields = ['created_at', 'is_active']

class UserOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOffer
        fields = ['id', 'free_products_remaining', 'free_estates_remaining', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ShopMediaSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    image = serializers.ImageField(use_url=True, allow_null=True, required=False)

    def validate(self, data):
        image = data.get('image')
        shop = data.get('shop')
        logger.debug(f"Validating ShopMedia: shop={shop.id if shop else None}, image={bool(image)}")
        if image is None and not ShopMedia.objects.filter(shop=shop).exists():
            raise serializers.ValidationError({"non_field_errors": "At least one image is required for the shop."})
        return data

    class Meta:
        model = ShopMedia
        fields = ['id', 'shop', 'image', 'is_primary']

class PromotionSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Promotion
        fields = ['id', 'shop', 'title', 'description', 'start_date', 'end_date', 'created_at', 'is_active']
        read_only_fields = ['created_at', 'is_active']

class EventSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Event
        fields = ['id', 'shop', 'title', 'description', 'start_time', 'end_time', 'is_free', 'ticket_price', 'created_at', 'is_active']
        read_only_fields = ['created_at', 'is_active']

class ServicesSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = Services
        fields = ['id', 'shop', 'name', 'description', 'price', 'duration', 'created_at', 'is_available']
        read_only_fields = ['created_at', 'is_available']

class ShopSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    services = ServicesSerializer(many=True, read_only=True)
    promotions = PromotionSerializer(many=True, read_only=True)
    events = EventSerializer(many=True, read_only=True)
    media = ShopMediaSerializer(many=True, read_only=True)
    subscription = SubscriptionSerializer(read_only=True)
    is_subscription_active = serializers.ReadOnlyField()
    image = serializers.ImageField(use_url=True, allow_null=True, required=False)  # Add image field
    subscription_warning = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            'id', 'user', 'name', 'phone', 'location', 'description', 'operating_hours',
            'social_media', 'university_partner', 'created_at', 'updated_at', 'is_active',
            'services', 'promotions', 'events', 'media', 'subscription', 'is_subscription_active',
            'image', 'subscription_warning'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'is_subscription_active']

    def get_subscription_warning(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        # Only show to the shop owner
        if user and user.is_authenticated and obj.user == user:
            subscription = getattr(obj, 'subscription', None)
            if subscription and subscription.status == subscription.Status.ACTIVE and subscription.end_date:
                now = timezone.now()
                if subscription.end_date - now < timedelta(days=7):
                    days_left = (subscription.end_date - now).days
                    return f"Your subscription will expire in {days_left} day(s). Please renew soon!"
        return None