from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from .views import (
    UniversityViewSet, CampusViewSet
)
from dashboard.admin import admin_site


router = DefaultRouter()
router.register(r'universities', UniversityViewSet)
router.register(r'campuses', CampusViewSet)

urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/payments/', include('payments.urls')),
    path('api/', include('marketplace.urls')),
    path('api/shops/', include('shops.urls')),
    path('api/estates/', include('estates.urls')),
    path('api/users/', include('users.urls')),
    path('accounts/', include('allauth.urls')),
    # Corrected line: Added a trailing slash to 'api/token'
    path('api/token/', TokenObtainPairView.as_view(), name='get_token'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    # YOUR PATTERNS
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/', include(router.urls)),  # Core app URLs (universities, locations)
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)