# users/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.utils.text import slugify
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponseRedirect
from django.urls import reverse

from users.models import NewUser

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            print(f"Existing social login for user: {sociallogin.user.email}")
            return
        
        email = sociallogin.account.extra_data.get('email')
        if not email:
            print("No email provided by social provider")
            return

        name = sociallogin.account.extra_data.get('name', email.split('@')[0])
        base_username = slugify(name)[:140]
        username = base_username
        counter = 1
        while NewUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        sociallogin.user.username = username
        request._social_login = True
        print(f"Pre-social login: email={email}, username={username}")

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Store tokens in session for debugging (optional)
        request.session['jwt_token'] = access_token
        request.session['refresh_token'] = refresh_token
        request.session['provider'] = sociallogin.account.provider
        print(f"Saved user: {user.email}, Access Token: {access_token[:10]}..., Refresh Token: {refresh_token[:10]}..., Provider: {sociallogin.account.provider}")
        
        return user

    def get_login_redirect_url(self, request):
        token = request.session.pop('jwt_token', None)
        refresh_token = request.session.pop('refresh_token', None)
        provider = request.session.pop('provider', 'unknown')
        
        if not token or not refresh_token:
            print("No tokens found in session, redirecting to login")
            return f"{settings.FRONTEND_URL}/login"
        
        # Create response with cookies
        response = HttpResponseRedirect(f"{settings.FRONTEND_URL}/social-callback?provider={provider}")
        response.set_cookie(
            'access_token',
            token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Strict',
            max_age=60 * 60 * 24 * 7  # 1 week
        )
        response.set_cookie(
            'refresh_token',
            refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Strict',
            max_age=60 * 60 * 24 * 30  # 1 month
        )
        print(f"Redirecting to: {response['Location']}")
        return response