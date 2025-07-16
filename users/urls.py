from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordChangeView,
    PasswordResetView, PasswordResetConfirmView
)
from dj_rest_auth.views import UserDetailsView as CustomUserDetailsView
from users.views import (
    CSRFView, CustomRegisterView, ProfileView, UserViewSet,
    get_campus_suggestions
)
from shops.views import UserOfferViewSet
from core.views import UniversityViewSet

# Create router for user viewsets
router = DefaultRouter()
router.register(r'', UserViewSet)  # Register without 'users' prefix since it's already in the URL path
router.register(r'universities', UniversityViewSet, basename='user-universities')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', CustomRegisterView.as_view(), name='rest_register'),
    path('auth/login/', LoginView.as_view(), name='rest_login'),
    path('auth/logout/', LogoutView.as_view(), name='rest_logout'),
    path('auth/password/change/', PasswordChangeView.as_view(), name='rest_password_change'),
    path('auth/password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
    path('auth/password/reset/confirm/<uidb64>/<token>/', 
         PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('get-csrf/', CSRFView.as_view(), name='get-csrf'),
    path('auth/user/', CustomUserDetailsView.as_view(), name='rest_user_details'),
    
    # User management endpoints
    path('auth/profile/', ProfileView.as_view(), name='user_profile'),
    path('offer/', UserOfferViewSet.as_view({'get': 'me'}), name='user-offer'),
    
    # Location and campus endpoints
    path('campus/suggestions/', get_campus_suggestions, name='get-campus-suggestions'),
    
    # Router URLs (includes /api/users/ and /api/users/public/)
    path('', include(router.urls)),
]