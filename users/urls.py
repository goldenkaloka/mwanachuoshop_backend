from django.urls import path, include
from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordChangeView,
    PasswordResetView, PasswordResetConfirmView
)
from dj_rest_auth.views import UserDetailsView as CustomUserDetailsView
from users.views import CSRFView, CustomRegisterView, ProfileView

urlpatterns = [
    path('auth/register/', CustomRegisterView.as_view(), name='rest_register'),
    path('auth/login/', LoginView.as_view(), name='rest_login'),
    path('auth/logout/', LogoutView.as_view(), name='rest_logout'),
    path('auth/password/change/', PasswordChangeView.as_view(), name='rest_password_change'),
    path('auth/password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
    path('auth/password/reset/confirm/<uidb64>/<token>/', 
         PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # Changed name
    path('get-csrf/', CSRFView.as_view(), name='get-csrf'),
    path('auth/user/', CustomUserDetailsView.as_view(), name='rest_user_details'),
    path('auth/profile/', ProfileView.as_view(), name='user_profile'),
]