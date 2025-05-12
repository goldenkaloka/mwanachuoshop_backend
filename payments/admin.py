from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import PaymentService, Payment


from django.utils.html import format_html

@admin.register(PaymentService)
class PaymentServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description_short')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description else ''
    description_short.short_description = 'Description'

class PaymentInline(GenericTabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('date_added', 'transaction_id')
    fields = ('service', 'amount', 'status', 'provider', 'date_added', 'transaction_id')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'amount', 'status', 'content_object_link', 'date_added')
    list_filter = ('status', 'service', 'date_added')
    search_fields = ('user__username', 'transaction_id', 'external_id')
    readonly_fields = ('date_added', 'content_object_link')
    fieldsets = (
        (None, {
            'fields': ('user', 'service', 'amount', 'status')
        }),
        ('Payment Details', {
            'fields': ('transaction_id', 'external_id', 'provider', 'account_number')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id', 'content_object_link')
        }),
        ('Timestamps', {
            'fields': ('date_added',)
        }),
    )
    
    def content_object_link(self, obj):
        if obj.content_object:
            return format_html('<a href="{}">{}</a>', 
                             obj.content_object.get_admin_url(),
                             str(obj.content_object))
        return None
    content_object_link.short_description = 'Related Object'