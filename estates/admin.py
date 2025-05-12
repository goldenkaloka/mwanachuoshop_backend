from django.contrib import admin
from django.utils.html import format_html
from .models import PropertyType, Property, PropertyImage

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    readonly_fields = ['image_preview']
    fields = ['image', 'image_preview', 'is_primary']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'

@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'owner', 
        'property_type', 
        'location', 
        'price',
        'video_status',
        'created_at'
    )
    list_filter = ('property_type', 'is_available', 'video_status')
    search_fields = ('title', 'location', 'owner__username')
    readonly_fields = (
        'slug', 
        'created_at', 
        'updated_at',
        'video_preview',
        'thumbnail_preview'
    )
    fieldsets = (
        ('Basic Info', {
            'fields': (
                'owner', 
                'property_type',
                'title',
                'slug',
                'features',
                'location',
                'price',
                'is_available'
            )
        }),
        ('Video Info', {
            'fields': (
                'video_name',
                'video_description',
                'video',
                'video_preview',
                'thumbnail',
                'thumbnail_preview',
                'duration',
                'hls_playlist',
                'video_status',
                'is_video_processing',
                'video_error_message'
            )
        }),
        ('Dates', {
            'fields': (
                'created_at',
                'updated_at'
            )
        }),
    )
    inlines = [PropertyImageInline]
    
    def video_preview(self, obj):
        if obj.video:
            return format_html(
                '<video width="300" controls><source src="{}"></video>',
                obj.video.url
            )
        return "-"
    video_preview.short_description = 'Video Preview'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height: 200px;"/>',
                obj.thumbnail.url
            )
        return "-"
    thumbnail_preview.short_description = 'Thumbnail Preview'

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px;"/>', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'