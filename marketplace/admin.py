from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from mptt.admin import DraggableMPTTAdmin
from .models import (
    Category, Brand, Attribute, 
    AttributeValue, Product, 
    ProductLine, ProductImage
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'order', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'


class ProductLineInline(admin.StackedInline):
    model = ProductLine
    extra = 1
    fields = ('sku', 'price', 'sale_price', 'cost_price', 'stock_qty', 'is_active', 'attribute_values')
    filter_horizontal = ('attribute_values',)
    inlines = [ProductImageInline]


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'slug', 'is_active', 'product_count')
    list_display_links = ('indented_title',)
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    mptt_level_indent = 20
    expand_tree_by_default = True
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            product_count=Count('products')
        )
    
    def product_count(self, instance):
        return instance.product_count
    product_count.short_description = 'Products'
    product_count.admin_order_field = 'product_count'

    actions = ['activate_categories', 'deactivate_categories']
    
    @admin.action(description='Activate selected categories')
    def activate_categories(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} categories were activated.')
    
    @admin.action(description='Deactivate selected categories')
    def deactivate_categories(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} categories were deactivated.')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'product_count', 'logo_preview')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            product_count=Count('products')
        )
    
    def product_count(self, obj):
        return obj.product_count
    product_count.short_description = 'Products'
    product_count.admin_order_field = 'product_count'
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.logo.url)
        return "-"
    logo_preview.short_description = 'Logo Preview'


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'value_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            value_count=Count('values')
        )
    
    def value_count(self, obj):
        return obj.value_count
    value_count.short_description = 'Values'
    value_count.admin_order_field = 'value_count'


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'slug', 'product_count')
    list_filter = ('attribute',)
    search_fields = ('value', 'slug')
    prepopulated_fields = {'slug': ('value',)}
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            product_count=Count('product_lines')
        )
    
    def product_count(self, obj):
        return obj.product_count
    product_count.short_description = 'Products'
    product_count.admin_order_field = 'product_count'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'brand', 'category', 
        'owner', 'shop', 'is_active', 
        'is_featured', 'created_at', 'product_line_count'
    )
    list_filter = (
        'is_active', 'is_featured', 'type', 
        'brand', 'category', 'created_at'
    )
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('owner', 'shop')
    inlines = [ProductLineInline]
    date_hierarchy = 'created_at'
    actions = ['activate_products', 'deactivate_products']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            product_line_count=Count('product_lines')
        )
    
    def product_line_count(self, obj):
        return obj.product_line_count
    product_line_count.short_description = 'Variants'
    product_line_count.admin_order_field = 'product_line_count'
    
    @admin.action(description='Activate selected products')
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} products were activated.')
    
    @admin.action(description='Deactivate selected products')
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} products were deactivated.')


@admin.register(ProductLine)
class ProductLineAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'sku', 'current_price', 
        'stock_qty', 'is_active', 'image_count'
    )
    list_filter = ('is_active', 'product__brand', 'product__category')
    search_fields = ('sku', 'product__name')
    raw_id_fields = ('product',)
    filter_horizontal = ('attribute_values',)
    inlines = [ProductImageInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            image_count=Count('images')
        )
    
    def image_count(self, obj):
        return obj.image_count
    image_count.short_description = 'Images'
    image_count.admin_order_field = 'image_count'
    
    def current_price(self, obj):
        return f"${obj.price:.2f}" if obj.price else "-"
    current_price.short_description = 'Price'
    current_price.admin_order_field = 'price'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product_line', 'image_preview', 'is_primary', 'order')
    list_filter = ('is_primary', 'product_line__product')
    search_fields = ('product_line__sku', 'product_line__product__name')
    raw_id_fields = ('product_line',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'