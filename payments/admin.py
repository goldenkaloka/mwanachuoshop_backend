from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import PaymentService, Payment, Wallet, WalletTransaction
from django.utils.html import format_html

@admin.register(PaymentService)
class PaymentServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    fields = ('name', 'price', 'description')


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'amount', 'description', 'created_at')
    fields = ('transaction_type', 'amount', 'description', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [WalletTransactionInline]
    ordering = ('-updated_at',)

    def has_add_permission(self, request):
        return False  # Wallets should be created via signals when users are created


class PaymentInline(GenericTabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_type', 'amount', 'status', 'date_added')
    fields = ('payment_type', 'amount', 'status', 'date_added')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'payment_type_display', 'service_display', 
        'amount', 'status_display', 'date_added', 'content_object_link'
    )
    list_filter = ('status', 'payment_type', 'date_added')
    search_fields = (
        'user__username', 'transaction_id', 'external_id',
        'amount', 'service__name'
    )
    readonly_fields = (
        'date_added', 'status', 'transaction_id', 'external_id',
        'provider', 'account_number', 'content_object_link'
    )
    fieldsets = (
        (None, {
            'fields': ('user', 'service', 'payment_type', 'amount', 'status')
        }),
        ('Payment Details', {
            'fields': (
                'transaction_id', 'external_id', 'provider', 
                'account_number', 'date_added'
            ),
            'classes': ('collapse',)
        }),
        ('Content Object', {
            'fields': ('content_object_link',),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-date_added',)
    actions = ['process_payments']

    def payment_type_display(self, obj):
        return obj.get_payment_type_display() if obj.payment_type else "-"
    payment_type_display.short_description = "Type"

    def service_display(self, obj):
        return str(obj.service) if obj.service else "-"
    service_display.short_description = "Service"

    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = "Status"

    def content_object_link(self, obj):
        if obj.content_object:
            return format_html(
                '<a href="{}">{}</a>',
                obj.content_object.get_admin_url(),
                str(obj.content_object)
            )
        return "-"
    content_object_link.short_description = "Content Object"

    def process_payments(self, request, queryset):
        processed = 0
        failed = 0
        for payment in queryset.filter(status=Payment.PaymentStatus.PENDING):
            try:
                payment.process_payment()
                processed += 1
            except Exception as e:
                failed += 1
                self.message_user(
                    request,
                    f"Failed to process payment {payment.id}: {str(e)}",
                    level='ERROR'
                )
        self.message_user(
            request,
            f"Successfully processed {processed} payments. {failed} failed."
        )
    process_payments.short_description = "Process selected pending payments"


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'wallet_user', 'transaction_type_display', 
        'amount', 'payment_link', 'created_at'
    )
    list_filter = ('transaction_type', 'created_at')
    search_fields = (
        'wallet__user__username', 'transaction_id', 'external_id',
        'payment__transaction_id', 'description'
    )
    readonly_fields = (
        'wallet', 'amount', 'transaction_type', 'payment_link', 
        'transaction_id', 'external_id', 'provider', 'account_number',
        'description', 'created_at'
    )
    fieldsets = (
        (None, {
            'fields': ('wallet', 'amount', 'transaction_type', 'payment_link')
        }),
        ('Transaction Details', {
            'fields': (
                'transaction_id', 'external_id', 'provider', 
                'account_number', 'description', 'created_at'
            ),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)

    def wallet_user(self, obj):
        return obj.wallet.user
    wallet_user.short_description = "User"
    wallet_user.admin_order_field = 'wallet__user'

    def transaction_type_display(self, obj):
        return obj.get_transaction_type_display()
    transaction_type_display.short_description = "Type"

    def payment_link(self, obj):
        if obj.payment:
            return format_html(
                '<a href="{}">{}</a>',
                obj.payment.get_admin_url(),
                str(obj.payment)
            )
        return "-"
    payment_link.short_description = "Payment"