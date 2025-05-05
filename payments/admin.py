from django.contrib import admin
from .models import PaymentService, Payment

@admin.register(PaymentService)
class PaymentServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    ordering = ('name',)

    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'Service Name'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'amount', 'status', 'date_added', 'transaction_id')
    list_filter = ('status', 'service', 'provider')
    search_fields = ('user__username', 'transaction_id', 'external_id', 'account_number')
    raw_id_fields = ('user', 'subscription')
    date_hierarchy = 'date_added'
    ordering = ('-date_added',)
    actions = ['mark_completed', 'mark_failed']

    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_completed.short_description = 'Mark selected payments as completed'

    def mark_failed(self, request, queryset):
        queryset.update(status='failed')
    mark_failed.short_description = 'Mark selected payments as failed'

    def get_service_name(self, obj):
        return obj.service.get_name_display()
    get_service_name.short_description = 'Service'