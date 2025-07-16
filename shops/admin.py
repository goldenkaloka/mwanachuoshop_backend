from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils import timezone
from datetime import timedelta
from django.contrib.admin import SimpleListFilter
import logging
from .models import Shop, ShopMedia, Promotion, Event, Services, UserOffer, Subscription


logger = logging.getLogger(__name__)

# Custom Filters
class ActivePromotionFilter(SimpleListFilter):
    title = 'is active'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('true', 'Active'),
            ('false', 'Inactive'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now()
            )
        if self.value() == 'false':
            return queryset.exclude(
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now()
            )
        return queryset

class ActiveEventFilter(SimpleListFilter):
    title = 'is active'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('true', 'Active'),
            ('false', 'Inactive'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now(),
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now()
            )
        if self.value() == 'false':
            return queryset.exclude(
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now(),
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now()
            )
        return queryset

class AvailableServicesFilter(SimpleListFilter):
    title = 'is available'
    parameter_name = 'is_available'

    def lookups(self, request, model_admin):
        return (
            ('true', 'Available'),
            ('false', 'Unavailable'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now()
            )
        if self.value() == 'false':
            return queryset.exclude(
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now()
            )
        return queryset

class ActiveSubscriptionFilter(SimpleListFilter):
    title = 'is active'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('true', 'Active'),
            ('false', 'Inactive'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(
                status=Subscription.Status.ACTIVE,
                end_date__gt=timezone.now()
            )
        if self.value() == 'false':
            return queryset.exclude(
                status=Subscription.Status.ACTIVE,
                end_date__gt=timezone.now()
            )
        return queryset

# Inlines
class ShopMediaInline(admin.TabularInline):
    model = ShopMedia
    extra = 1
    fields = ('image', 'is_primary')
    readonly_fields = ('image',)
    can_delete = True

class PromotionInline(admin.TabularInline):
    model = Promotion
    extra = 1
    fields = ('title', 'description', 'start_date', 'end_date', 'is_active')
    readonly_fields = ('is_active',)

class EventInline(admin.TabularInline):
    model = Event
    extra = 1
    fields = ('title', 'start_time', 'end_time', 'is_free', 'ticket_price', 'is_active')
    readonly_fields = ('is_active',)

class ServicesInline(admin.TabularInline):
    model = Services
    extra = 1
    fields = ('name', 'price', 'duration', 'is_available')
    readonly_fields = ('is_available',)

# Admin Classes
@admin.register(Shop)
class ShopAdmin(ModelAdmin):
    list_display = ('name', 'user', 'is_active', 'campus')
    search_fields = ('name',)
    list_filter = ('is_active',)
    default_lon = 39.2
    default_lat = -6.8
    default_zoom = 6
    readonly_fields = ('created_at', 'updated_at', 'is_subscription_active')
    inlines = [ShopMediaInline, PromotionInline, EventInline, ServicesInline]
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'phone', 'campus', 'description')
        }),
        ('Details', {
            'fields': ('image', 'operating_hours', 'social_media', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'is_subscription_active')
        }),
    )
    actions = ['deactivate_shop', 'reactivate_shop']

    def deactivate_shop(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} shop(s).")
        logger.info(f"Admin deactivated {updated} shop(s) via action.")
    deactivate_shop.short_description = "Deactivate selected shops"

    def reactivate_shop(self, request, queryset):
        updated = 0
        for shop in queryset:
            if shop.is_subscription_active():
                shop.is_active = True
                shop.save()
                updated += 1
        self.message_user(request, f"Reactivated {updated} shop(s) with active subscriptions.")
        logger.info(f"Admin reactivated {updated} shop(s) via action.")
    reactivate_shop.short_description = "Reactivate selected shops with active subscriptions"

@admin.register(ShopMedia)
class ShopMediaAdmin(ModelAdmin):
    list_display = ('shop', 'is_primary', 'image')
    list_filter = ('is_primary',)
    search_fields = ('shop__name',)
    readonly_fields = ('image',)

@admin.register(Promotion)
class PromotionAdmin(ModelAdmin):
    list_display = ('title', 'shop', 'start_date', 'end_date', 'is_active')
    list_filter = (ActivePromotionFilter, 'start_date', 'end_date')
    search_fields = ('title', 'shop__name')
    readonly_fields = ('created_at', 'is_active')

@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ('title', 'shop', 'start_time', 'end_time', 'is_free', 'is_active')
    list_filter = (ActiveEventFilter, 'is_free', 'start_time')
    search_fields = ('title', 'shop__name')
    readonly_fields = ('created_at', 'is_active')

@admin.register(Services)
class ServicesAdmin(ModelAdmin):
    list_display = ('name', 'shop', 'price', 'duration', 'is_available')
    list_filter = (AvailableServicesFilter,)
    search_fields = ('name', 'shop__name')
    readonly_fields = ('created_at', 'is_available')

@admin.register(UserOffer)
class UserOfferAdmin(ModelAdmin):
    list_display = ('user', 'free_products_remaining', 'free_estates_remaining', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['reset_free_offers']

    def reset_free_offers(self, request, queryset):
        for offer in queryset:
            offer.free_products_remaining = 0
            offer.free_estates_remaining = 0
            offer.save()
        self.message_user(request, "Reset free offers for selected users.")

@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ('shop', 'user', 'status', 'start_date', 'end_date', 'is_trial', 'is_active')
    list_filter = ('status', 'is_trial', ActiveSubscriptionFilter)
    search_fields = ('shop__name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'is_active')
    actions = ['extend_subscription', 'cancel_subscription']

    def extend_subscription(self, request, queryset):
        for subscription in queryset:
            subscription.extend()
        self.message_user(request, "Extended selected subscriptions.")

    def cancel_subscription(self, request, queryset):
        for subscription in queryset:
            subscription.cancel()
        self.message_user(request, "Cancelled selected subscriptions.")