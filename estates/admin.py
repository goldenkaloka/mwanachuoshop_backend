from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
import logging


from .models import Property, PropertyType, PropertyImage
from payments.models import Payment

logger = logging.getLogger(__name__)

# Inline for PropertyImage to display images within Property admin
class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image', 'is_primary', 'created_at', 'image_preview')
    readonly_fields = ('created_at', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

# Admin for PropertyType
@admin.register(PropertyType)
class PropertyTypeAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

    def get_readonly_fields(self, request, obj=None):
        # Make name read-only when editing to prevent accidental changes
        if obj:
            return ('name',)
        return ()

# Admin for Property
@admin.register(Property)
class PropertyAdmin(ModelAdmin):
    list_display = ('title', 'is_available', 'location', 'campus_display')
    search_fields = ('title', 'location')
    list_filter = ('is_available', 'campus', 'property_type')
    default_lon = 39.2
    default_lat = -6.8
    default_zoom = 6
    readonly_fields = ('slug', 'created_at', 'updated_at')
    inlines = [PropertyImageInline]
    actions = ['activate_properties', 'deactivate_properties']
    fieldsets = (
        (None, {
            'fields': ('owner', 'property_type', 'title', 'slug', 'location', 'price', 'is_available')
        }),
        ('Details', {
            'fields': ('features', 'campus')
        }),
    )

    def campus_display(self, obj):
        """Display campuses as a comma-separated list"""
        campuses = obj.campus.all()
        if campuses:
            return ', '.join([campus.name for campus in campuses])
        return "No campus selected"
    campus_display.short_description = 'Campuses'

    def activate_properties(self, request, queryset):
        """Bulk activate properties by processing payments."""
        content_type = ContentType.objects.get_for_model(Property)
        for property_obj in queryset:
            if property_obj.is_available:
                self.message_user(request, f"Property {property_obj.title} is already active.", level='warning')
                continue
            try:
                property_obj.activate_property()
                self.message_user(request, f"Property {property_obj.title} activated successfully.", level='success')
            except Exception as e:
                self.message_user(request, f"Failed to activate {property_obj.title}: {e}", level='error')

    def deactivate_properties(self, request, queryset):
        for property_obj in queryset:
            if not property_obj.is_available:
                self.message_user(request, f"Property {property_obj.title} is already inactive.", level='warning')
                continue
            property_obj.is_available = False
            property_obj.save()
            self.message_user(request, f"Property {property_obj.title} deactivated successfully.", level='success')

# Admin for PropertyImage
@admin.register(PropertyImage)
class PropertyImageAdmin(ModelAdmin):
    list_display = ('property', 'is_primary', 'created_at', 'image_preview')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('property__title', 'property__location')
    readonly_fields = ('created_at', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image Preview'