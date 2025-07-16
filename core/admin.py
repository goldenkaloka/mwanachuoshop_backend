from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import University, Campus

@admin.register(University)
class UniversityAdmin(ModelAdmin):
    list_display = ['name', 'short_name', 'radius_km', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'short_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'short_name', 'is_active')
        }),
        ('Location Settings', {
            'fields': ('location', 'radius_km')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Campus)
class CampusAdmin(ModelAdmin):
    list_display = ['name', 'university', 'address', 'is_active', 'created_at']
    list_filter = ['university', 'is_active', 'created_at']
    search_fields = ['name', 'address', 'university__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'university', 'address', 'is_active')
        }),
        ('Location Settings', {
            'fields': ('location',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 