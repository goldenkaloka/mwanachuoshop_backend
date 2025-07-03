from decimal import Decimal
import os
from pathlib import Path
from datetime import timedelta
import environ

# Import ZenoPay for payment integration
import dj_database_url
from zenopay import ZenoPay  # Adjust the import path if necessary

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# django-environ setup
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'mptt',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'users',
    'marketplace',
    'corsheaders',
    'estates',
    'shops',
    'payments',
    'phonenumber_field',
    'rest_framework',
    'django_filters',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',
    'rest_framework_simplejwt',
    'allauth.socialaccount',
    'django_cleanup.apps.CleanupConfig',
    'django_q',
    'drf_spectacular',
    'django_extensions',
    'video_transcoding',
    'storages',
    'django_pesapal',
    'django_pesapalv3',
    "debug_toolbar",
    'allauth.socialaccount.providers.google', 
    'allauth.socialaccount.providers.apple', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
     "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = 'core.urls'
SITE_ID = 1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database configuration for Render PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mwanachuoshop_database',
        'USER': 'mwanachuoshop_database_user',
        'PASSWORD': '1AW0GCZL5u6ugISSVtJiODVJmPgvvnFw',
        'HOST': 'dpg-d1hhpjndiees73bdmehg-a.oregon-postgres.render.com',  # Internal hostname for Render
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,  # Timeout after 10 seconds
        },
    }
}


AWS_ACCESS_KEY_ID = os.getenv('CLOUDFLARE_R2_ACCESS_KEY_ID', 'c02e50bd8f808ebea69917e8a475c2a4')
AWS_SECRET_ACCESS_KEY = os.getenv('CLOUDFLARE_R2_SECRET_ACCESS_KEY', 'bcf277ea30d80e011fb1828f250486f21c83e9b832b94f112fbb26a83819bb86')
AWS_STORAGE_BUCKET_NAME = os.getenv('CLOUDFLARE_R2_BUCKET_NAME', 'mwanachuoshop-media')
AWS_S3_ENDPOINT_URL = os.getenv('CLOUDFLARE_R2_ENDPOINT_URL', 'https://34b85ecebdccd8f57b5414d007372647.r2.cloudflarestorage.com')
AWS_S3_REGION_NAME = 'auto'
AWS_S3_FILE_OVERWRITE = False
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_CUSTOM_DOMAIN = os.getenv('CLOUDFLARE_R2_CUSTOM_DOMAIN', 'pub-80453e25e7504aa88343419d0a831d1d.r2.dev')
AWS_S3_SIGNATURE_VERSION = 's3v4'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cloudflare Stream configuration
CLOUDFLARE_ACCOUNT_ID = '34b85ecebdccd8f57b5414d007372647'
CLOUDFLARE_STREAM_API_TOKEN = 'HKvNOwsjv5hfTXeB3cdsKqUsPf0moHNkuvW-XNgO'
CLOUDFLARE_STREAM_API_BASE_URL = os.getenv('CLOUDFLARE_STREAM_API_BASE_URL', 'https://api.cloudflare.com/client/v4')

# Email configuration for Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('EMAIL_HOST_USER')

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Dar_es_Salaam'
USE_I18N = True
USE_TZ = True

# # Static files
# STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# STATICFILES_FINDERS = [
#     'django.contrib.staticfiles.finders.FileSystemFinder',
#     'django.contrib.staticfiles.finders.AppDirectoriesFinder',
# ]

# # Video processing directories (to be updated for Wasabi)
# HLS_OUTPUT_DIR = os.path.join(MEDIA_ROOT, 'hls')
# THUMBNAIL_DIR = os.path.join(MEDIA_ROOT, 'thumbnails')
# os.makedirs(HLS_OUTPUT_DIR, exist_ok=True)
# os.makedirs(THUMBNAIL_DIR, exist_ok=True)

CORS_ALLOW_ALL_ORIGINS = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.NewUser' 
SOCIALACCOUNT_STORE_TOKENS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

REST_AUTH = {
    'USE_JWT': True,
    'OLD_PASSWORD_FIELD_ENABLED': True,
    'LOGOUT_ON_PASSWORD_CHANGE': True,
    'REGISTER_SERIALIZER': 'users.serializers.CustomRegisterSerializer',
    'USER_DETAILS_SERIALIZER': 'users.serializers.CustomUserDetailsSerializer',
    'JWT_AUTH_COOKIE': 'access_token',  # Name of access token cookie
    'JWT_AUTH_REFRESH_COOKIE': 'refresh_token',  # Name of refresh token cookie
    'JWT_AUTH_HTTPONLY': True,  # Enable HTTP-only cookies
    'JWT_AUTH_SAMESITE': 'Strict'
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=4),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# Allauth settings
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
SOCIALACCOUNT_ADAPTER = 'users.adapters.CustomSocialAccountAdapter'

# Redirect to React frontend after social login
# The following URL is overridden by our custom adapter's get_login_redirect_url method
# SOCIALACCOUNT_LOGIN_REDIRECT_URL = 'http://localhost:8080/dashboard'
LOGIN_REDIRECT_URL = 'http://localhost:8080/dashboard'
SOCIALACCOUNT_LOGIN_ON_GET = True  

FRONTEND_URL = env('FRONTEND_URL')

# --- CORS (Cross-Origin Resource Sharing) settings ---

# For development, allowing all origins is convenient.
# WARNING: This is insecure for production. Set to False when using CORS_ALLOWED_ORIGINS.


# For a secure production environment, you should replace CORS_ALLOW_ALL_ORIGINS = True
# with a specific list of allowed domains.
# CORS_ALLOWED_ORIGINS = [
#     os.getenv('FRONTEND_URL', 'http://localhost:8080'),
#     'https://master-relevant-flounder.ngrok-free.app',
#     # Add your production frontend domain here, e.g., 'https://www.mwanachuoshop.com'
# ]

# This is crucial for allowing the frontend to send credentials (like cookies or auth headers).
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = ['https://master-relevant-flounder.ngrok-free.app', env('FRONTEND_URL')]

# Pesapal settings
PESAPAL_DEMO = env.bool('PESAPAL_DEMO', default=True)
PESAPAL_CONSUMER_KEY = env('PESAPAL_CONSUMER_KEY')
PESAPAL_CONSUMER_SECRET = env('PESAPAL_CONSUMER_SECRET')
# The IPN URL you register on your Pesapal merchant dashboard.
# Example: 'https://master-relevant-flounder.ngrok-free.app/v3/payments/callback/pesapal/'
PESAPAL_NOTIFICATION_ID = env('PESAPAL_NOTIFICATION_ID')
PESAPAL_CALLBACK_URL = env('PESAPAL_CALLBACK_URL')
PESAPAL_TRANSACTION_DEFAULT_REDIRECT_URL = 'http://localhost:3000/wallet/success'  # Frontend success page
PESAPAL_ALLOWED_IPS = []  # Disable IP restrictions for testing
PESAPAL_API_URL = 'https://cybqa.pesapal.com/pesapalv3/api' if PESAPAL_DEMO else 'https://pay.pesapal.com/v3/api'

# Parse Redis URL from environment
redis_url = env('REDIS_URL', default='redis://localhost:6379/0')
from urllib.parse import urlparse
url = urlparse(redis_url)

Q_CLUSTER = {
    'name': 'VideoProcessingCluster',
    'workers': 2,  # Reduced for production stability
    'recycle': 500,  # Restart workers after 500 tasks
    'retry': 60 * 5,  # Retry after 5 minutes (reduced from 31)
    'timeout': 60 * 15,  # Timeout after 15 minutes (reduced from 30)
    'compress': True,  # Compress task data
    'save_limit': 250,  # Keep last 250 tasks for monitoring
    'queue_limit': 50,  # Reduced queue limit
    'cpu_affinity': 1,  # Bind each worker to 1 CPU core
    'label': 'Video Processing',
    'catch_up': False,  # Don't catch up on missed tasks
    'sync': False,  # Async mode
    'redis': {
        'host': url.hostname,
        'port': url.port,
        'db': int(url.path.lstrip('/') or 0),
        'username': url.username or None,
        'password': url.password or None,
        'ssl': url.scheme == 'rediss',
        'socket_connect_timeout': 10,
        'socket_timeout': 10,
        'retry_on_timeout': True,
    },
}


# Jazzmin settings (unchanged)
JAZZMIN_SETTINGS = {
    'site_title': 'Mwanachuoshop',
    'site_header': 'Mwanachuoshop admin',
    'site_brand': 'Mwanachuoshop',
    'welcome_sign': 'Welcome to Mwanachuoshop admin panel',
    'copyright': 'Mwanachuoshop Ltd',
    'search_model': ['products.Product', 'auth.User'],
    'show_ui_builder': True,
    'navigation_expanded': True,
    'icons': {
        'auth.user': 'fas fa-user',
        'auth.Group': 'fas fa-users',
        'products.Product': 'fas fa-box',
        'products.Category': 'fas fa-tags',
        'products.Brand': 'fas fa-copyright',
        'products.Attribute': 'fas fa-list',
        'products.AttributeValue': 'fas fa-list-alt',
        'products.ProductImage': 'fas fa-image',
        'products.WhatsAppClick': 'fas fa-whatsapp',
    },
    'topmenu_links': [
        {'name': 'Home', 'url': 'admin:index', 'permissions': ['auth.view_user']},
        {'name': 'Support', 'url': 'https://github.com/farridav/django-jazzmin/issues', 'new_window': True},
        {'model': 'auth.User'},
        {'app': 'products'},
    ],
    'usermenu_links': [
        {'name': 'Support', 'url': 'https://github.com/farridav/django-jazzmin/issues', 'new_window': True},
        {'model': 'auth.user'},
    ],
    'theme': 'default',
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
    'related_modal_active': False,
    'show_sidebar': True,
    'navigation_expanded': True,
    'changeform_format': 'horizontal_tabs',
    'changeform_format_overrides': {
        'auth.user': 'collapsible',
        'auth.group': 'vertical_tabs',
    },
    'language_chooser': False,
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-primary',
    'accent': 'accent-primary',
    'navbar': 'navbar-white navbar-light',
    'no_navbar_border': False,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-primary',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': False,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'default',
    'button_classes': {
        'primary': 'btn-outline-primary',
        'secondary': 'btn-outline-secondary',
        'info': 'btn-outline-info',
        'warning': 'btn-outline-warning',
        'danger': 'btn-outline-danger',
        'success': 'btn-outline-success',
    },
    'actions_sticky_top': False,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Mwanachuoshop API',
    'DESCRIPTION': 'mwanachuoshop api is an api which will serve as a basis for all mwanachuoshop system management',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

SHOP_TRIAL_DAYS = 30
SHOP_TRIAL_MINUTES = 120
USER_OFFER_DEFAULTS = {
    'free_products_remaining': 20,
    'free_estates_remaining': 5,
}
PAYMENT_CURRENCY = 'TZS'
SHOP_SUBSCRIPTION_PRICE = Decimal('5000.00')
ZENOPAY_ALLOWED_IPS = ['203.0.113.1', '203.0.113.2']


SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': env('GOOGLE_OAUTH_CLIENT_ID'),
            'secret': env('GOOGLE_OAUTH_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
}
