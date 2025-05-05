from rest_framework import serializers
from .models import Shop, ShopMedia, Promotion, Event, Services, Subscription, UserOffer
import logging

logger = logging.getLogger(__name__)

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'status', 'start_date', 'end_date', 'is_trial', 'created_at']

class UserOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOffer
        fields = ['id', 'free_products_remaining', 'free_estates_remaining', 'shop_trial_end_date', 'created_at']

class ShopMediaSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    image = serializers.ImageField(use_url=True, allow_null=True, required=False)
    video = serializers.FileField(use_url=True, allow_null=True, required=False)

    def validate(self, data):
        image = data.get('image')
        video = data.get('video')
        shop = data.get('shop')
        logger.debug(f"Validating ShopMedia: shop={shop.id if shop else None}, image={bool(image)}, video={bool(video)}")
        if not image and not video:
            raise serializers.ValidationError({"non_field_errors": "Either image or video must be provided."})
        if image and video:
            raise serializers.ValidationError({"non_field_errors": "Only one of image or video can be provided."})
        return data

    class Meta:
        model = ShopMedia
        fields = ['id', 'shop', 'image', 'video', 'is_primary']

class PromotionSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())

    class Meta:
        model = Promotion
        fields = ['id', 'shop', 'title', 'description', 'start_date', 'end_date', 'created_at']

class EventSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())

    class Meta:
        model = Event
        fields = ['id', 'shop', 'title', 'description', 'start_time', 'end_time', 'is_free', 'ticket_price', 'created_at']

class ServicesSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())

    class Meta:
        model = Services
        fields = ['id', 'shop', 'name', 'description', 'price', 'duration', 'created_at']

class ShopSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    services = ServicesSerializer(many=True, read_only=True)
    promotions = PromotionSerializer(many=True, read_only=True)
    events = EventSerializer(many=True, read_only=True)
    media = ShopMediaSerializer(many=True, read_only=True)
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = Shop
        fields = [
            'id', 'user', 'name', 'phone', 'location', 'description', 'operating_hours',
            'social_media', 'university_partner', 'created_at', 'updated_at',
            'services', 'promotions', 'events', 'media', 'subscription'
        ]