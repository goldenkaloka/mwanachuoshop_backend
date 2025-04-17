from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import SubscriptionPlan, ShopSubscription, Shop, ShopMedia, ShopService, ShopPromotion

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'duration_days', 'is_trial', 'active', 'max_products_display')
    list_filter = ('is_trial', 'active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'price', 'duration_days', 'active')
        }),
        ('Features', {
            'fields': ('is_trial', 'max_products', 'can_add_products', 'product_price'),
            'description': 'Configure what this plan allows users to do'
        })
    )
    
    def max_products_display(self, obj):
        return "Unlimited" if obj.max_products == 0 else obj.max_products
    max_products_display.short_description = 'Max Products'

@admin.register(ShopSubscription)
class ShopSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('shop_link', 'plan_link', 'start_date', 'end_date', 'days_remaining', 'is_active', 'is_trial')
    list_filter = ('is_active', 'is_trial', 'plan')
    search_fields = ('shop__name', 'shop__owner__username')
    date_hierarchy = 'start_date'
    readonly_fields = ('days_remaining', 'created_at')
    
    def shop_link(self, obj):
        url = reverse('admin:shops_shop_change', args=[obj.shop.id])
        return format_html('<a href="{}">{}</a>', url, obj.shop.name)
    shop_link.short_description = 'Shop'
    
    def plan_link(self, obj):
        url = reverse('admin:shops_subscriptionplan_change', args=[obj.plan.id])
        return format_html('<a href="{}">{}</a>', url, obj.plan.name)
    plan_link.short_description = 'Plan'
    
    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'Days Left'

class ShopMediaInline(admin.TabularInline):
    model = ShopMedia
    extra = 1
    fields = ('media_type', 'image_preview', 'image', 'video', 'is_primary', 'uploaded_at')
    readonly_fields = ('image_preview', 'uploaded_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'

class ShopServiceInline(admin.TabularInline):
    model = ShopService
    extra = 1
    fields = ('name', 'description', 'price', 'duration')
    readonly_fields = ('clean',)  # This won't show in admin but prevents errors

class ShopPromotionInline(admin.TabularInline):
    model = ShopPromotion
    extra = 1
    fields = ('title', 'content', 'start_date', 'end_date', 'is_active', 'views')
    readonly_fields = ('is_active', 'views')

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_link', 'region', 'is_active', 'created_at', 'active_subscription_link')
    list_filter = ('is_active', 'region')
    search_fields = ('name', 'owner__username', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    inlines = [ShopMediaInline, ShopServiceInline, ShopPromotionInline]
    actions = ['activate_shops', 'deactivate_shops']
    fieldsets = (
        (None, {
            'fields': ('owner', 'name', 'slug', 'description')
        }),
        ('Contact Information', {
            'fields': ('contact_whatsapp', 'location', 'region')
        }),
        ('Status', {
            'fields': ('is_active',),
            'classes': ('collapse',)
        })
    )
    
    def owner_link(self, obj):
        url = reverse('admin:users_newuser_change', args=[obj.owner.id])
        return format_html('<a href="{}">{}</a>', url, obj.owner.username)
    owner_link.short_description = 'Owner'
    
    def active_subscription_link(self, obj):
        sub = obj.active_subscription
        if sub:
            url = reverse('admin:shops_shopsubscription_change', args=[sub.id])
            return format_html('<a href="{}">{}</a>', url, sub.plan.name)
        return "-"
    active_subscription_link.short_description = 'Active Plan'
    
    @admin.action(description='Activate selected shops')
    def activate_shops(self, request, queryset):
        queryset.update(is_active=True)
    
    @admin.action(description='Deactivate selected shops')
    def deactivate_shops(self, request, queryset):
        queryset.update(is_active=False)

@admin.register(ShopMedia)
class ShopMediaAdmin(admin.ModelAdmin):
    list_display = ('shop_link', 'media_type', 'image_preview', 'is_primary', 'uploaded_at')
    list_filter = ('media_type', 'is_primary', 'shop')
    search_fields = ('shop__name',)
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('image_preview', 'uploaded_at')
    
    def shop_link(self, obj):
        url = reverse('admin:shops_shop_change', args=[obj.shop.id])
        return format_html('<a href="{}">{}</a>', url, obj.shop.name)
    shop_link.short_description = 'Shop'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'

@admin.register(ShopService)
class ShopServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop_link', 'price', 'duration')
    list_filter = ('shop',)
    search_fields = ('name', 'description', 'shop__name')
    raw_id_fields = ('shop',)
    
    def shop_link(self, obj):
        url = reverse('admin:shops_shop_change', args=[obj.shop.id])
        return format_html('<a href="{}">{}</a>', url, obj.shop.name)
    shop_link.short_description = 'Shop'

@admin.register(ShopPromotion)
class ShopPromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'shop_link', 'start_date', 'end_date', 'is_active', 'views')
    list_filter = ('shop',)
    search_fields = ('title', 'content', 'shop__name')
    date_hierarchy = 'start_date'
    readonly_fields = ('views', 'is_active')
    
    def shop_link(self, obj):
        url = reverse('admin:shops_shop_change', args=[obj.shop.id])
        return format_html('<a href="{}">{}</a>', url, obj.shop.name)
    shop_link.short_description = 'Shop'
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = 'Active'