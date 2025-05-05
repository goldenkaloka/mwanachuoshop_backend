from django.contrib import admin
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage

# Category Admin with MPTT support
@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'product_count')
    list_filter = ('is_active',)
    search_fields = ('name',)
    mptt_level_indent = 20
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

# Brand Admin with image preview
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo_preview', 'product_count')
    search_fields = ('name',)
    readonly_fields = ('logo_preview',)
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.logo.url)
        return "-"
    logo_preview.short_description = 'Logo Preview'
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

# Attribute Admin
@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'value_count')
    search_fields = ('name',)
    
    def value_count(self, obj):
        return obj.values.count()
    value_count.short_description = 'Values'

# AttributeValue Admin with category filtering
class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'category', 'product_count')
    list_filter = ('attribute', 'category')
    search_fields = ('value', 'attribute__name', 'category__name')
    
    def product_count(self, obj):
        return obj.product_lines.count()
    product_count.short_description = 'Products'

# ProductImage Inline
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'

# Product Admin with advanced filtering
class ProductAttributeFilter(admin.SimpleListFilter):
    title = 'Attributes'
    parameter_name = 'attribute'
    
    def lookups(self, request, model_admin):
        return [(a.id, a.name) for a in Attribute.objects.all()]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(attribute_values__attribute_id=self.value()).distinct()
        return queryset

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'price', 'owner', 'created_at', 'attribute_values_display')
    list_filter = ('brand', 'category', ProductAttributeFilter, 'created_at')
    search_fields = ('name', 'description', 'brand__name', 'category__name')
    raw_id_fields = ('owner', 'shop')
    inlines = [ProductImageInline]
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('attribute_values',)
    
    def attribute_values_display(self, obj):
        return ", ".join([str(av) for av in obj.attribute_values.all()])
    attribute_values_display.short_description = 'Attributes'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'brand', 'category', 'price')
        }),
        ('Relationships', {
            'fields': ('owner', 'shop', 'attribute_values')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# ProductImage Admin
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_preview', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('product__name',)
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'