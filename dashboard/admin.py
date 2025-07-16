from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from users.models import NewUser, Profile
from shops.models import Shop, ShopMedia, Promotion, Event, Services, UserOffer, Subscription
from marketplace.models import Category, Brand, Attribute, AttributeValue, Product, ProductImage, WhatsAppClick
from estates.models import Property, PropertyType, PropertyImage
from payments.models import PaymentService, Payment, Wallet, WalletTransaction
from core.models import University
from users.admin import NewUserAdmin, ProfileAdmin
from shops.admin import ShopAdmin, ShopMediaAdmin, PromotionAdmin, EventAdmin, ServicesAdmin, UserOfferAdmin, SubscriptionAdmin
from marketplace.admin import CategoryAdmin, BrandAdmin, AttributeAdmin, AttributeValueAdmin, ProductAdmin, ProductImageAdmin, WhatsAppClickAdmin
from estates.admin import PropertyAdmin, PropertyTypeAdmin, PropertyImageAdmin
from payments.admin import PaymentServiceAdmin, PaymentAdmin, WalletAdmin, WalletTransactionAdmin
from core.admin import UniversityAdmin
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q, Max
from unfold.sites import UnfoldAdminSite
from django.db.models.functions import ExtractYear, ExtractMonth

class AnalyticsAdminSite(UnfoldAdminSite):
    site_header = "Mwanachuoshop Admin"
    site_title = "Mwanachuoshop Admin Portal"
    index_title = "Welcome to Mwanachuoshop Admin"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analytics/', self.admin_view(self.analytics_view), name='analytics'),
            path('', self.admin_view(self.analytics_view), name='index'),  # Make analytics the homepage
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        return self.analytics_view(request)

    def analytics_view(self, request):
        now = datetime.now()
        month_ago = now - timedelta(days=30)
        week_ago = now - timedelta(days=7)
        today = now.date()

        # KPIs
        total_users = NewUser.objects.count()
        active_users = NewUser.objects.filter(is_active=True).count()
        new_users_month = NewUser.objects.filter(start_date__gte=month_ago).count()
        total_shops = Shop.objects.count()
        active_shops = Shop.objects.filter(is_active=True).count()
        new_shops_month = Shop.objects.filter(created_at__gte=month_ago).count()
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        new_products_month = Product.objects.filter(created_at__gte=month_ago).count()
        total_properties = Property.objects.count()
        new_properties_month = Property.objects.filter(created_at__gte=month_ago).count()
        total_universities = University.objects.count()
        active_universities = University.objects.filter(is_active=True).count()
        total_payments = Payment.objects.count()
        revenue_all = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        revenue_month = Payment.objects.filter(date_added__gte=month_ago).aggregate(total=Sum('amount'))['total'] or 0
        revenue_today = Payment.objects.filter(date_added__date=today).aggregate(total=Sum('amount'))['total'] or 0

        # Most popular university
        top_university = University.objects.annotate(user_count=Count('campuses__profiles')).order_by('-user_count').first()
        # Most active user/shop/product
        most_active_user = NewUser.objects.annotate(num_products=Count('products')).order_by('-num_products').first()
        most_active_shop = Shop.objects.annotate(num_products=Count('products')).order_by('-num_products').first()
        most_active_product = Product.objects.annotate(num_views=Count('whatsapp_clicks')).order_by('-num_views').first()

        # Trends
        user_growth = NewUser.objects.annotate(
            year=ExtractYear('start_date'),
            month=ExtractMonth('start_date')
        ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')
        shop_growth = Shop.objects.annotate(
            year=ExtractYear('created_at'),
            month=ExtractMonth('created_at')
        ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')
        product_growth = Product.objects.annotate(
            year=ExtractYear('created_at'),
            month=ExtractMonth('created_at')
        ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')
        revenue_trend = Payment.objects.annotate(
            year=ExtractYear('date_added'),
            month=ExtractMonth('date_added')
        ).values('year', 'month').annotate(total=Sum('amount')).order_by('year', 'month')
        top_universities = University.objects.annotate(user_count=Count('campuses__profiles')).order_by('-user_count')[:5]
        top_shops = Shop.objects.annotate(num_products=Count('products')).order_by('-num_products')[:5]
        top_products = Product.objects.annotate(num_views=Count('whatsapp_clicks')).order_by('-num_views')[:5]

        # Recent activity
        recent_users = NewUser.objects.order_by('-start_date')[:5]
        recent_shops = Shop.objects.order_by('-created_at')[:5]
        recent_payments = Payment.objects.order_by('-date_added')[:5]
        recent_products = Product.objects.order_by('-created_at')[:5]
        recent_properties = Property.objects.order_by('-created_at')[:5]

        # Health & Engagement
        inactive_users = NewUser.objects.filter(last_login__lt=week_ago)[:5]
        inactive_shops = Shop.objects.filter(updated_at__lt=week_ago)[:5]
        pending_shops = Shop.objects.filter(is_active=False)[:5]
        flagged_products = Product.objects.filter(is_active=False)[:5]

        context = dict(
            self.each_context(request),
            # KPIs
            total_users=total_users,
            active_users=active_users,
            new_users_month=new_users_month,
            total_shops=total_shops,
            active_shops=active_shops,
            new_shops_month=new_shops_month,
            total_products=total_products,
            active_products=active_products,
            new_products_month=new_products_month,
            total_properties=total_properties,
            new_properties_month=new_properties_month,
            total_universities=total_universities,
            active_universities=active_universities,
            total_payments=total_payments,
            revenue_all=revenue_all,
            revenue_month=revenue_month,
            revenue_today=revenue_today,
            # Top performers
            top_university=top_university,
            most_active_user=most_active_user,
            most_active_shop=most_active_shop,
            most_active_product=most_active_product,
            # Trends
            user_growth_dates=[f"{x['year']}-{x['month']:02d}" for x in user_growth],
            user_growth_counts=[x['count'] for x in user_growth],
            shop_growth_dates=[f"{x['year']}-{x['month']:02d}" for x in shop_growth],
            shop_growth_counts=[x['count'] for x in shop_growth],
            product_growth_dates=[f"{x['year']}-{x['month']:02d}" for x in product_growth],
            product_growth_counts=[x['count'] for x in product_growth],
            revenue_trend_dates=[f"{x['year']}-{x['month']:02d}" for x in revenue_trend],
            revenue_trend_totals=[x['total'] for x in revenue_trend],
            top_universities=top_universities,
            top_shops=top_shops,
            top_products=top_products,
            # Recent activity
            recent_users=recent_users,
            recent_shops=recent_shops,
            recent_payments=recent_payments,
            recent_products=recent_products,
            recent_properties=recent_properties,
            # Health & Engagement
            inactive_users=inactive_users,
            inactive_shops=inactive_shops,
            pending_shops=pending_shops,
            flagged_products=flagged_products,
        )
        return TemplateResponse(request, "admin/analytics.html", context)

# Register the custom admin site
admin_site = AnalyticsAdminSite(name='analytics_admin')

# Register all major models with their ModelAdmin classes
admin_site.register(NewUser, NewUserAdmin)
admin_site.register(Profile, ProfileAdmin)
admin_site.register(Shop, ShopAdmin)
admin_site.register(ShopMedia, ShopMediaAdmin)
admin_site.register(Promotion, PromotionAdmin)
admin_site.register(Event, EventAdmin)
admin_site.register(Services, ServicesAdmin)
admin_site.register(UserOffer, UserOfferAdmin)
admin_site.register(Subscription, SubscriptionAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Brand, BrandAdmin)
admin_site.register(Attribute, AttributeAdmin)
admin_site.register(AttributeValue, AttributeValueAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(ProductImage, ProductImageAdmin)
admin_site.register(WhatsAppClick, WhatsAppClickAdmin)
admin_site.register(Property, PropertyAdmin)
admin_site.register(PropertyType, PropertyTypeAdmin)
admin_site.register(PropertyImage, PropertyImageAdmin)
admin_site.register(PaymentService, PaymentServiceAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(Wallet, WalletAdmin)
admin_site.register(WalletTransaction, WalletTransactionAdmin)
admin_site.register(University, UniversityAdmin)
