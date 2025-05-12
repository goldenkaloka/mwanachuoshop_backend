from django.contrib import admin
from .models import Shop, ShopMedia, Promotion, Event, Services, UserOffer, Subscription

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'location', 'university_partner', 'created_at', 'is_subscription_active')
    list_filter = ('university_partner', 'created_at')
    search_fields = ('name', 'location', 'description')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(ShopMedia)
class ShopMediaAdmin(admin.ModelAdmin):
    list_display = ('shop', 'is_primary', 'image', 'video')
    list_filter = ('is_primary',)
    search_fields = ('shop__name',)
    raw_id_fields = ('shop',)

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'shop', 'start_date', 'end_date', 'created_at')
    list_filter = ('start_date', 'end_date')
    search_fields = ('title', 'description', 'shop__name')
    raw_id_fields = ('shop',)
    date_hierarchy = 'start_date'

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'shop', 'start_time', 'end_time', 'is_free', 'ticket_price')
    list_filter = ('is_free', 'start_time')
    search_fields = ('title', 'description', 'shop__name')
    raw_id_fields = ('shop',)
    date_hierarchy = 'start_time'

@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'price', 'duration', 'created_at')
    search_fields = ('name', 'description', 'shop__name')
    raw_id_fields = ('shop',)
    date_hierarchy = 'created_at'

@admin.register(UserOffer)
class UserOfferAdmin(admin.ModelAdmin):
    list_display = ('user', 'free_products_remaining', 'free_estates_remaining', 'shop_trial_end_date', 'is_shop_trial_active')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('shop', 'user', 'status', 'start_date', 'end_date', 'is_trial', 'is_active')
    list_filter = ('status', 'is_trial')
    search_fields = ('shop__name', 'user__username')
    raw_id_fields = ('user', 'shop')
    date_hierarchy = 'start_date'