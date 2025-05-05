from django.contrib import admin
from .models import PropertyType, Property, PropertyImage, Video
from django.utils.html import format_html

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    readonly_fields = ['thumbnail_preview']

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
        return "-"
    thumbnail_preview.short_description = 'Preview'

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1
    readonly_fields = ['status_display', 'thumbnail_preview']
    
    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Status'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="100" height="auto" />', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = 'Thumbnail'

@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'property_count')
    search_fields = ('name',)
    
    def property_count(self, obj):
        return obj.properties.count()
    property_count.short_description = 'Properties'

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'property_type', 'location', 'price', 'is_available', 'created_at')
    list_filter = ('property_type', 'is_available', 'created_at')
    search_fields = ('title', 'location', 'owner__username')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PropertyImageInline, VideoInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'property_type', 'title', 'slug')
        }),
        ('Details', {
            'fields': ('features', 'location', 'price', 'is_available')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'is_primary', 'created_at', 'thumbnail_preview')
    list_filter = ('is_primary',)
    search_fields = ('property__title',)
    readonly_fields = ('thumbnail_preview',)
    
    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
        return "-"
    thumbnail_preview.short_description = 'Preview'

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('name', 'property', 'status_display', 'duration', 'created_at', 'video_preview')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'property__title')
    readonly_fields = ('status_display', 'video_preview', 'thumbnail_preview', 'created_at', 'updated_at')
    
    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Status'
    
    def video_preview(self, obj):
        if obj.video:
            return format_html(
                '<video width="150" height="auto" controls><source src="{}"></video>',
                obj.video.url
            )
        return "-"
    video_preview.short_description = 'Preview'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="100" height="auto" />', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = 'Thumbnail'