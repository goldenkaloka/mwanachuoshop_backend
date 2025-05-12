from mptt.admin import MPTTModelAdmin
from django.contrib import admin
from django.utils.html import format_html
from .models import *

@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    mptt_level_indent = 20

class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'values_count')
    search_fields = ('name',)
    inlines = [AttributeValueInline]
    
    def values_count(self, obj):
        return obj.values.count()
    values_count.short_description = 'Values Count'

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'logo_preview')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.logo.url)
        return None
    logo_preview.short_description = 'Logo Preview'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return None
    image_preview.short_description = 'Preview'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'brand', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'brand', 'created_at')
    search_fields = ('name', 'description', 'brand__name')
    readonly_fields = ('created_at', 'updated_at', 'attribute_values_list')
    filter_horizontal = ('attribute_values',)
    inlines = [ProductImageInline]
    actions = ['activate_products', 'deactivate_products']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Pricing & Inventory', {
            'fields': ('price',)
        }),
        ('Relationships', {
            'fields': ('owner', 'shop', 'category', 'brand')
        }),
        ('Attributes', {
            'fields': ('attribute_values', 'attribute_values_list')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def attribute_values_list(self, obj):
        return ", ".join([str(av) for av in obj.attribute_values.all()])
    attribute_values_list.short_description = 'Current Attributes'
    
    @admin.action(description='Activate selected products')
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} products activated')
    
    @admin.action(description='Deactivate selected products')
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} products deactivated')

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_preview', 'is_primary')
    list_filter = ('is_primary', 'product__category')
    search_fields = ('product__name',)
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return None
    image_preview.short_description = 'Preview'