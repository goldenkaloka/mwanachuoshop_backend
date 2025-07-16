from decimal import Decimal
import os
from pathlib import Path
from datetime import timedelta
import environ
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
except ImportError:
    sentry_sdk = None
    DjangoIntegration = None

# Import ZenoPay for payment integration
import dj_database_url
from zenopay import ZenoPay  # Adjust the import path if necessary

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Remove django-environ setup
# env = environ.Env(
#     DEBUG=(bool, False)
# )
# environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Application definition
INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # 'django.contrib.gis',  # Commented out - using simplified location system
    'core',  # Add core app for University and Location models
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

    'storages',
    'django_pesapal',
    'django_pesapalv3',
    'allauth.socialaccount.providers.google', 
    'allauth.socialaccount.providers.apple', 
    'dashboard',
    'django.contrib.gis',
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
]

# Add CSP and security headers for production
if not DEBUG:
    MIDDLEWARE.insert(1, 'csp.middleware.CSPMiddleware')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_REFERRER_POLICY = 'same-origin'
    # Content Security Policy
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_SCRIPT_SRC = ("'self'", 'https://cdn.jsdelivr.net')
    CSP_STYLE_SRC = ("'self'", 'https://fonts.googleapis.com', 'https://cdn.jsdelivr.net')
    CSP_FONT_SRC = ("'self'", 'https://fonts.gstatic.com')
    CSP_IMG_SRC = ("'self'", 'data:', 'https://*')
    CSP_CONNECT_SRC = ("'self'", 'https://*')
    CSP_FRAME_SRC = ("'self'",)
    CSP_OBJECT_SRC = ("'none'",)
    CSP_BASE_URI = ("'self'",)
    CSP_FORM_ACTION = ("'self'",)

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




DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'mwanachuoshop',
        'USER': 'mwanachuouser',
        'PASSWORD': 'mwanachuopass',
        'HOST': 'db',
        'PORT': '5432',
    }
}

# # Database configuration for Render PostgreSQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'mwanachuoshop_database',
#         'USER': 'mwanachuoshop_database_user',
#         'PASSWORD': '1AW0GCZL5u6ugISSVtJiODVJmPgvvnFw',
#         'HOST': 'dpg-d1hhpjndiees73bdmehg-a.oregon-postgres.render.com',  # Internal hostname for Render
#         'PORT': '5432',
#         'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
#         'OPTIONS': {
#             'connect_timeout': 10,  # Timeout after 10 seconds
#         },
#     }
# }



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
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cloudflare Stream configuration
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID', '34b85ecebdccd8f57b5414d007372647')
CLOUDFLARE_STREAM_API_TOKEN = os.getenv('CLOUDFLARE_STREAM_API_TOKEN', 'HKvNOwsjv5hfTXeB3cdsKqUsPf0moHNkuvW-XNgO')
CLOUDFLARE_STREAM_API_BASE_URL = os.getenv('CLOUDFLARE_STREAM_API_BASE_URL', 'https://api.cloudflare.com/client/v4')

# Email configuration for Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Custom User Model
AUTH_USER_MODEL = 'users.NewUser'

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
USE_TZ = TruTICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# STATICFILES_FINDERS = [
#     'django.contrib.staticfiles.finders.FileSystemFinder',
#     'django.contrib.staticfiles.finders.AppDirectoriesFinder',
# ]

# # Video processing directories (to be updated for Wasabi)
# HLS_OUTPUT_DIR = os.path.join(MEDIA_ROOT, 'hls')
# THUMBNAIL_DIR = os.path.join(MEDIA_ROOT, 'thumbnails')
# os.makedirs(HLS_OUTPUT_DIR, exist_ok=True)
# os.makedirs(THUMBNAIL_DIR, exist_ok=True)

# --- CORS (Cross-Origin Resource Sharing) settings ---

# For development, allow all origins
CORS_ALLOW_ALL_ORIGINS = True

# For production, use the following and set CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    # Add your production frontend domain(s) here
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'https://master-relevant-flounder.ngrok-free.app',
    os.getenv('FRONTEND_URL', 'http://localhost:8080')
]

# Pesapal settings
PESAPAL_DEMO = os.getenv('PESAPAL_DEMO', 'True').lower() in ('true', '1', 'yes')
PESAPAL_CONSUMER_KEY = os.getenv('PESAPAL_CONSUMER_KEY', '')
PESAPAL_CONSUMER_SECRET = os.getenv('PESAPAL_CONSUMER_SECRET', '')
# The IPN URL you register on your Pesapal merchant dashboard.
# Example: 'https://master-relevant-flounder.ngrok-free.app/v3/payments/callback/pesapal/'
PESAPAL_NOTIFICATION_ID = os.getenv('PESAPAL_NOTIFICATION_ID', '')
PESAPAL_CALLBACK_URL = os.getenv('PESAPAL_CALLBACK_URL', '')
PESAPAL_TRANSACTION_DEFAULT_REDIRECT_URL = 'http://localhost:3000/wallet/success'  # Frontend success page
PESAPAL_ALLOWED_IPS = []  # Disable IP restrictions for testing
PESAPAL_API_URL = 'https://cybqa.pesapal.com/pesapalv3/api' if PESAPAL_DEMO else 'https://pay.pesapal.com/v3/api'

# Parse Redis URL from environment
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
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





SPECTACULAR_SETTINGS = {
    'TITLE': 'Mwanachuoshop API',
    'DESCRIPTION': 'mwanachuoshop api is an api which will serve as a basis for all mwanachuoshop system management',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

SHOP_TRIAL_DAYS = 30
# SHOP_TRIAL_MINUTES = 120  # Commented out to prevent DEBUG mode override
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
            'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
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

UNFOLD = {
    "SITE_TITLE": "Mwanachuoshop Admin",
    "SITE_HEADER": "Mwanachuoshop Admin",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "COLLAPSIBLE_NAV": True,
    "SIDEBAR": {
        "items": [
            {"label": "Analytics", "url": "/admin/analytics/", "icon": "bar-chart"},
            {"app": "users", "icon": "users"},
            {"app": "shops", "icon": "shopping-bag"},
            {"app": "marketplace", "icon": "package"},
            {"app": "estates", "icon": "home"},
            {"app": "payments", "icon": "credit-card"},
            {"app": "core", "icon": "map-pin"},
        ]
    },
}

# Security: Add security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Security: Fix default permissions
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'core.exception_handler.custom_exception_handler',
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
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Changed from 4 days
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

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8080')

# Security: Disable debug toolbar in production
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

# Sentry integration
SENTRY_DSN = os.getenv('SENTRY_DSN', None)
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'development')
if SENTRY_DSN and sentry_sdk:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=SENTRY_ENVIRONMENT,
        traces_sample_rate=0.2,
        send_default_pii=True,
    )

# Structured logging for production
import sys
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": %(message)s, "module": "%(module)s", "process": %(process)d, "thread": %(thread)d}',
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s %(name)s %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'json' if not DEBUG else 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
