from django.contrib import admin
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
class PropertyTypeAdmin(admin.ModelAdmin):
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
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'location', 'property_type', 'price', 'is_available', 'created_at', 'video_status')
    list_filter = ('is_available', 'property_type', 'created_at')
    search_fields = ('title', 'location', 'owner__username', 'owner__email')
    readonly_fields = ('slug', 'created_at', 'updated_at', 'duration', 'thumbnail_preview', 'video_preview', 'transcoded_video_link')
    inlines = [PropertyImageInline]
    actions = ['activate_properties', 'deactivate_properties']
    fieldsets = (
        (None, {
            'fields': ('owner', 'property_type', 'title', 'slug', 'location', 'price', 'is_available')
        }),
        ('Details', {
            'fields': ('features', 'video_description')
        }),
        ('Video', {
            'fields': ('video', 'video_name', 'video_preview', 'thumbnail', 'thumbnail_preview', 'duration', 'transcoded_video', 'transcoded_video_link')
        }),
    )

    def video_status(self, obj):
        if obj.transcoded_video:
            return obj.transcoded_video.status
        return 'No Video'
    video_status.short_description = 'Video Status'

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.thumbnail.url)
        return "No Thumbnail"
    thumbnail_preview.short_description = 'Thumbnail Preview'

    def video_preview(self, obj):
        if obj.video:
            return format_html('<video width="200" controls><source src="{}" type="video/mp4">Your browser does not support the video tag.</video>', obj.video.url)
        return "No Video"
    video_preview.short_description = 'Video Preview'

    def transcoded_video_link(self, obj):
        if obj.transcoded_video:
            video_id = obj.transcoded_video.id
            url = reverse('admin:video_transcoding_video_change', args=[video_id])
            return format_html('<a href="{}">{}</a>', url, obj.transcoded_video)
        return "No Transcoded Video"
    transcoded_video_link.short_description = 'Transcoded Video'

    def activate_properties(self, request, queryset):
        """Bulk activate properties by processing payments."""
        content_type = ContentType.objects.get_for_model(Property)
        for property_obj in queryset:
            if property_obj.is_available:
                self.message_user(request, f"Property {property_obj.title} is already active.", level='warning')
                continue
            try:
                payment_amount = (Decimal(property_obj.price) * Decimal('0.01')).quantize(Decimal('0.01'))
                logger.info(f"Admin activating property {property_obj.id} with payment amount: {payment_amount} TZS")
                with transaction.atomic():
                    payment = Payment.objects.create(
                        user=property_obj.owner,
                        amount=payment_amount,
                        status=Payment.PaymentStatus.PENDING,
                        content_type=content_type,
                        object_id=property_obj.id,
                        payment_type=Payment.PaymentType.ESTATE,
                        service=None
                    )
                    payment.process_payment()
                    property_obj.is_available = True
                    property_obj.save()
                    logger.info(f"Property {property_obj.id} activated by admin for user {property_obj.owner.username}")
                    self.message_user(request, f"Property {property_obj.title} activated successfully.", level='success')
            except ValidationError as e:
                logger.error(f"Failed to activate property {property_obj.id}: {str(e)}")
                self.message_user(request, f"Failed to activate property {property_obj.title}: {str(e)}", level='error')
    activate_properties.short_description = "Activate selected properties"

    def deactivate_properties(self, request, queryset):
        """Bulk deactivate properties."""
        for property_obj in queryset:
            if not property_obj.is_available:
                self.message_user(request, f"Property {property_obj.title} is already inactive.", level='warning')
                continue
            property_obj.is_available = False
            property_obj.save()
            logger.info(f"Property {property_obj.id} deactivated by admin")
            self.message_user(request, f"Property {property_obj.title} deactivated successfully.", level='success')
    deactivate_properties.short_description = "Deactivate selected properties"

    def get_readonly_fields(self, request, obj=None):
        # Make slug and timestamps read-only
        readonly = ['slug', 'created_at', 'updated_at', 'thumbnail_preview', 'video_preview', 'transcoded_video_link']
        if obj and obj.transcoded_video:
            readonly.append('duration')
        return readonly

# Admin for PropertyImage
@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'is_primary', 'created_at', 'image_preview')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('property__title', 'property__location')
    readonly_fields = ('created_at', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image Preview'