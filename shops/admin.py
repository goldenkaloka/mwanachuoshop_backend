from django.contrib import admin
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
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'location', 'is_active', 'is_subscription_active', 'created_at')
    list_filter = ('is_active', 'university_partner')
    search_fields = ('name', 'user__username', 'user__email', 'phone', 'location')
    readonly_fields = ('created_at', 'updated_at', 'is_subscription_active')
    inlines = [ShopMediaInline, PromotionInline, EventInline, ServicesInline]
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'phone', 'location', 'description')
        }),
        ('Details', {
            'fields': ('image', 'operating_hours', 'social_media', 'university_partner', 'is_active')
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
class ShopMediaAdmin(admin.ModelAdmin):
    list_display = ('shop', 'is_primary', 'image')
    list_filter = ('is_primary',)
    search_fields = ('shop__name',)
    readonly_fields = ('image',)

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'shop', 'start_date', 'end_date', 'is_active')
    list_filter = (ActivePromotionFilter, 'start_date', 'end_date')
    search_fields = ('title', 'shop__name')
    readonly_fields = ('created_at', 'is_active')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'shop', 'start_time', 'end_time', 'is_free', 'is_active')
    list_filter = (ActiveEventFilter, 'is_free', 'start_time')
    search_fields = ('title', 'shop__name')
    readonly_fields = ('created_at', 'is_active')

@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'price', 'duration', 'is_available')
    list_filter = (AvailableServicesFilter,)
    search_fields = ('name', 'shop__name')
    readonly_fields = ('created_at', 'is_available')

@admin.register(UserOffer)
class UserOfferAdmin(admin.ModelAdmin):
    list_display = ('user', 'free_products_remaining', 'free_estates_remaining', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['reset_free_offers']

    def reset_free_offers(self, request, queryset):
        updated = queryset.update(
            free_products_remaining=20,
            free_estates_remaining=5
        )
        self.message_user(request, f"Reset free offers for {updated} user(s).")
        logger.info(f"Admin reset free offers for {updated} user(s) via action.")
    reset_free_offers.short_description = "Reset free products and estates to defaults"

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('shop', 'user', 'status', 'start_date', 'end_date', 'is_trial', 'is_active')
    list_filter = ('status', 'is_trial', ActiveSubscriptionFilter)
    search_fields = ('shop__name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'is_active')
    actions = ['extend_subscription', 'cancel_subscription']

    def extend_subscription(self, request, queryset):
        updated = 0
        for subscription in queryset:
            subscription.end_date = timezone.now() + timedelta(days=30)
            subscription.is_trial = False
            subscription.status = Subscription.Status.ACTIVE
            subscription.shop.is_active = True
            subscription.shop.save(update_fields=['is_active'])
            subscription.save()
            updated += 1
            logger.info(f"Admin extended subscription {subscription.id} for shop {subscription.shop.id}")
        self.message_user(request, f"Extended {updated} subscription(s) by 30 days.")
    extend_subscription.short_description = "Extend selected subscriptions by 30 days"

    def cancel_subscription(self, request, queryset):
        updated = queryset.update(
            status=Subscription.Status.CANCELED,
            end_date=timezone.now()
        )
        for subscription in queryset:
            subscription.shop.is_active = False
            subscription.shop.save()
            logger.info(f"Admin canceled subscription {subscription.id} for shop {subscription.shop.id}")
        self.message_user(request, f"Canceled {updated} subscription(s).")
    cancel_subscription.short_description = "Cancel selected subscriptions"