from django.contrib import admin
from .models import Shop, ShopMedia, Promotion, Event, Services


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'location', 'university_partner', 'created_at')
    list_filter = ('university_partner', 'created_at')
    search_fields = ('name', 'location', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'phone', 'location')
        }),
        ('Details', {
            'fields': ('description', 'operating_hours', 'social_media', 'university_partner')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    raw_id_fields = ('user',)  # Improves performance for large user bases


@admin.register(ShopMedia)
class ShopMediaAdmin(admin.ModelAdmin):
    list_display = ('shop', 'is_primary', 'image', 'video')
    list_filter = ('is_primary',)
    search_fields = ('shop__name',)
    list_select_related = ('shop',)  # Optimizes queries
    raw_id_fields = ('shop',)


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'shop', 'start_date', 'end_date', 'created_at')
    list_filter = ('start_date', 'end_date')
    search_fields = ('title', 'description', 'shop__name')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at',)
    raw_id_fields = ('shop',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'shop', 'start_time', 'end_time', 'is_free', 'ticket_price')
    list_filter = ('is_free', 'start_time')
    search_fields = ('title', 'description', 'shop__name')
    date_hierarchy = 'start_time'
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('shop', 'title', 'description')
        }),
        ('Event Details', {
            'fields': ('start_time', 'end_time', 'is_free', 'ticket_price')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    raw_id_fields = ('shop',)


@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'price', 'duration', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'shop__name')
    readonly_fields = ('created_at',)
    raw_id_fields = ('shop',)