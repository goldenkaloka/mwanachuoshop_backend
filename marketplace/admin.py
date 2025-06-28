from django.contrib import admin
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage, WhatsAppClick
from mptt.admin import MPTTModelAdmin

@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    mptt_level_indent = 20

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('categories',)
    list_select_related = ('created_by',)

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'category', 'value')
    list_filter = ('attribute', 'category')
    search_fields = ('value',)
    list_select_related = ('attribute', 'category')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'owner', 'shop', 'price', 'condition', 'is_active', 'created_at')
    list_filter = ('is_active', 'condition', 'brand', 'category', 'shop')
    search_fields = ('name', 'description')
    list_select_related = ('brand', 'category', 'owner', 'shop')
    filter_horizontal = ('attribute_values',)
    date_hierarchy = 'created_at'
    actions = ['activate_selected_products']
    
    def activate_selected_products(self, request, queryset):
        for product in queryset:
            if not product.is_active:
                try:
                    product.activate_product()
                    self.message_user(request, f"Successfully activated {product.name}")
                except Exception as e:
                    self.message_user(request, f"Failed to activate {product.name}: {str(e)}", level='error')
    activate_selected_products.short_description = "Activate selected products"

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('product__name',)
    list_select_related = ('product',)

@admin.register(WhatsAppClick)
class WhatsAppClickAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'clicked_at', 'ip_address')
    list_filter = ('clicked_at',)
    search_fields = ('product__name', 'user__username')
    date_hierarchy = 'clicked_at'
    list_select_related = ('product', 'user')