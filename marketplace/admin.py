from django.contrib import admin
from django import forms
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage, WhatsAppClick

# Custom form for Product to validate attribute_values
class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        attribute_values = cleaned_data.get('attribute_values')
        if category and attribute_values:
            for attr_value in attribute_values:
                if attr_value.category != category:
                    raise forms.ValidationError(
                        f"Attribute value '{attr_value}' does not belong to category '{category}'."
                    )
        return cleaned_data

# Inline for ProductImage
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_primary')

# Simplified admin classes
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'category')
    list_filter = ('attribute', 'category')
    search_fields = ('value',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'brand', 'category', 'price', 'is_active')
    list_filter = ('brand', 'category', 'is_active')
    search_fields = ('name',)
    inlines = [ProductImageInline]
    filter_horizontal = ('attribute_values',)

    def save_model(self, request, obj, form, change):
        # Save Product first to generate an ID
        obj.save()
        super().save_model(request, obj, form, change)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary')
    search_fields = ('product__name',)

@admin.register(WhatsAppClick)
class WhatsAppClickAdmin(admin.ModelAdmin):
    list_display = ('product', 'clicked_at')
    list_filter = ('clicked_at',)
    search_fields = ('product__name',)