from django.contrib import admin
from unfold.admin import ModelAdmin
from mptt.admin import MPTTModelAdmin

from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage, WhatsAppClick

@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    mptt_level_indent = 20

@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Attribute)
class AttributeAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(AttributeValue)
class AttributeValueAdmin(ModelAdmin):
    list_display = ('value', 'attribute', 'category')
    list_filter = ('attribute', 'category')
    search_fields = ('value', 'attribute__name', 'category__name')

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'shop', 'is_active', 'get_campuses')
    search_fields = ('name',)
    list_filter = ('is_active',)
    default_lon = 39.2  # Example: Dar es Salaam
    default_lat = -6.8
    default_zoom = 6
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'owner', 'brand', 'category', 'price', 'condition', 'campus')
        }),
        ('Location Information', {
            'fields': ()
        }),
        ('Shop Information', {
            'fields': ('shop',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_campuses(self, obj):
        return ", ".join([c.name for c in obj.campus.all()])
    get_campuses.short_description = 'Campuses'

@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ('product', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('product__name',)

@admin.register(WhatsAppClick)
class WhatsAppClickAdmin(ModelAdmin):
    list_display = ('product', 'user', 'clicked_at')
    list_filter = ('clicked_at',)
    search_fields = ('product__name', 'user__username')
    readonly_fields = ('clicked_at',)