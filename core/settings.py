from decimal import Decimal
import os
from pathlib import Path
from datetime import timedelta
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-*8+ke8y3(wy-jawy-_mngl=&4e$#1q5^9)#kr*xa9^_=i_!57p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
    "corsheaders",
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

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",

]

ROOT_URLCONF = 'core.urls'
SITE_ID = 1
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS':  [os.path.join(BASE_DIR, 'templates')],
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


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mwanachuoshop',       
        'USER': 'mwanachuoshop_user',       
        'PASSWORD': 'U3ZxJIpUDe2EU3ET6irYfi1ujvCnXGMG', 
        'HOST': 'dpg-d10rs463jp1c739aa60g-a.oregon-postgres.render.com',       
        'PORT': '5432',                    
    }
}



# Email configuration for Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'mwanachuoshop@gmail.com'  
EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'  
DEFAULT_FROM_EMAIL = 'mwanachuoshop@gmail.com'  




# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Dar_es_Salaam'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # For production

# Additional locations of static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media settings
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Video processing directories
HLS_OUTPUT_DIR = os.path.join(MEDIA_ROOT, 'hls')
THUMBNAIL_DIR = os.path.join(MEDIA_ROOT, 'thumbnails')

# Create directories if they don't exist
os.makedirs(HLS_OUTPUT_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)


# Media files (user uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

CORS_ALLOW_ALL_ORIGINS = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'users.NewUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow all by default
    ],

     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}




REST_AUTH = {
    'USE_JWT': True,
    'OLD_PASSWORD_FIELD_ENABLED': True,
    'LOGOUT_ON_PASSWORD_CHANGE': True,
    'REGISTER_SERIALIZER': 'users.serializers.CustomRegisterSerializer',
    'USER_DETAILS_SERIALIZER': 'users.serializers.CustomUserDetailsSerializer',
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




CSRF_TRUSTED_ORIGINS = [
    'https://master-relevant-flounder.ngrok-free.app'
]


import os
from zenopay import ZenoPay

# Load ZenoPay credentials securely from environment variables
ZENOPAY_ACCOUNT_ID = 'your_zenopay_account_id'  # Replace with your actual ZenoPay account ID
ZENOPAY_API_KEY = 'your_zenopay_api_key'  # Replace with your actual ZenoPay API key
ZENOPAY_SECRET_KEY = 'your_zenopay_secret_key'  # Replace with your actual ZenoPay secret key


ZENOPAY_CLIENT = ZenoPay(account_id=ZENOPAY_ACCOUNT_ID)
ZENOPAY_CLIENT.api_key = ZENOPAY_API_KEY
ZENOPAY_CLIENT.secret_key = ZENOPAY_SECRET_KEY


# ZenoPay Settings
ZENOPAY_API_BASE_URL="https://api.zeno.africa"
ZENOPAY_WEBHOOK_URL="https://master-relevant-flounder.ngrok-free.app/api/payments/zenopay-callback/"
ZENOPAY_ALLOWED_IPS="203.0.113.1,203.0.113.2"


# Celery Configuration

# Django-Q Configuration
Q_CLUSTER = {
    'name': 'VideoProcessingCluster',
    'workers': 4,  # Number of worker processes
    'recycle': 500,
    'retry': 60 * 31,  
    'timeout': 60 * 30,  # 30 minute timeout for video processing
    'compress': True,  # Compress task data
    'save_limit': 250,  # Limit saved tasks
    'queue_limit': 100,  # Maximum queued tasks
    'cpu_affinity': 1,  # Better for CPU-intensive tasks
    'label': 'Video Processing',
    'redis': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0, 
        'password': None,
        'socket_timeout': None,
        'unix_socket_path': None
    }
}


JAZZMIN_SETTINGS = {
    # Title on the brand (19 chars max)
    "site_title": "Mwanachuoshop",
    "site_header": "Mwanachuoshop admin",
    "site_brand": "Mwanachuoshop",
    "site_logo": None,
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Welcome to Mwanachuoshop admin panel",
    "copyright": "Mwanachuoshop Ltd",
    "search_model": ["products.Product", "auth.User"],
    
    # UI Tweaks
    "show_ui_builder": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "products",
        "products.product",
        "products.category",
        "products.brand",
        "products.attribute",
        "auth",
    ],
    
    # Custom icons
    "icons": {
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "products.Product": "fas fa-box",
        "products.Category": "fas fa-tags",
        "products.Brand": "fas fa-copyright",
        "products.Attribute": "fas fa-list",
        "products.AttributeValue": "fas fa-list-alt",
        "products.ProductImage": "fas fa-image",
        "products.WhatsAppClick": "fas fa-whatsapp",
    },
    
    # Top menu configuration
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.User"},
        {"app": "products"},
    ],
    
    # Custom links
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.user"}
    ],
    
    # Theme options
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    
    # Related modal
    "related_modal_active": False,
    
    # Custom CSS/JS
    "custom_css": None,
    "custom_js": None,
    
    # Show sidebar
    "show_sidebar": True,
    
    # Navigation menu
    "navigation_expanded": True,
    
    # Misc
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs"
    },
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-outline-info",
        "warning": "btn-outline-warning",
        "danger": "btn-outline-danger",
        "success": "btn-outline-success"
    },
    "actions_sticky_top": False
}
   

SPECTACULAR_SETTINGS = {
    'TITLE': 'Mwanachuoshop API',
    'DESCRIPTION': 'mwanachuoshop api is an api which will server as a basis for all mwanachuoshop system management',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}


SHOP_TRIAL_DAYS = 30
SHOP_TRIAL_MINUTES = 120 
USER_OFFER_DEFAULTS = {
    'free_products_remaining': 20,
    'free_estates_remaining': 5
}
PAYMENT_CURRENCY = 'TZS'
SHOP_SUBSCRIPTION_PRICE = Decimal('5000.00')
ZENOPAY_ALLOWED_IPS = ['<ZenoPay_IP1>', '<ZenoPay_IP2>']  # Replace with actual IPs
