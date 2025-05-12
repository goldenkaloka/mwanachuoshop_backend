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
    'rest_framework_simplejwt.token_blacklist',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',
    'rest_framework_simplejwt',
    'allauth.socialaccount',
    'django_cleanup.apps.CleanupConfig',
    'django_q',

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

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

TIME_ZONE = 'UTC'

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

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
   'http://172.31.7.161:5173',
   'https://master-relevant-flounder.ngrok-free.app',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = ['accept', 'authorization', 'content-type', 'origin', 'x-csrftoken']

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'users.NewUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    

}


REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh',
    'JWT_AUTH_HTTPONLY': False,
    'OLD_PASSWORD_FIELD_ENABLED': True,
    'LOGOUT_ON_PASSWORD_CHANGE': True,
    'REGISTER_SERIALIZER': 'users.serializers.CustomRegisterSerializer',
    'USER_DETAILS_SERIALIZER': 'users.serializers.CustomUserDetailsSerializer',
}



SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
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


# AzamPay Configuration
AZAMPAY_CONFIG = {
    'APP_NAME': 'mwanachuoshop',
    'CLIENT_ID': '0fbddf98-36f9-4051-b5f5-10ebd0301cb7',
    'CLIENT_SECRET': 'X9b04f+B7nIQgK7+Q/9+cHYyljhiYYEVg78dzsBJ58028354m/klOw2Y80j4N5qNX0Tkwa07UzS0+fdagpHYc+o9ZCY9CvPazzEpgKUQFn69fjJKm4BEUX5Nzr/EiMxwUpzGdFvuTdeBmOWN4OoJMalXQ9R/UuR60sxhQNRKys5poU/zmGlfMRTHFg62yiCwFJzyhLV/HycA/YOV/G5AwDPUPJJIsQBl31RCmzydebeuCeZ2KmdzLTKQqKaAU1aUkE98CEFfdZlcsHa9U2z+yUSEtE8S94UM3kbytImKMzECb+b0xV5FWlJbbgUIOVjvreFvKL4k3v5gacCkcaZAvy5Z9OJhKBLg3uq54/PrIi339g0TeerLrYIwvCwrdRhcUdOuZ7MqRaN3FgO+Kw84iIpzpoDH5jwaFaLafcoBVJqbO5q1gZwj0oAeIh93ZsY6yGzbqY4I1o9EZyHIOc3f2vtq4Ozms8oAw2h5kYfjo4tWxyIWcaTQBJNY8QsGof8Qyp41mKRo0YFWS2jy4DQ0r69ihAAY4tEeXe1IcLenc6g2o67yY7vbNzggS5ym4EspsZfjbpIjx0D0Q6OojNKkb26LxWMojpBXlh1W3h/WHsBTMfIyizbFOOh7UVnyKHxFZoOAMDg86NXnCB4w/btGZvW7NW+XQkR+XmidWPA97OI=',
    'SANDBOX': True,  
}

# AZAMPAY_CLIENT = Azampay(
#     app_name=AZAMPAY_CONFIG['APP_NAME'],
#     client_id=AZAMPAY_CONFIG['CLIENT_ID'],
#     client_secret=AZAMPAY_CONFIG['CLIENT_SECRET'],
#     sandbox=AZAMPAY_CONFIG['SANDBOX'],
# )

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'payments.views': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}


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
    "welcome_sign": "Welcome to Mwanachuoshop admin panel",
    
    # UI Tweaks
    "show_ui_builder": True,  # Enable UI configurator (for live customization)
    "navigation_expanded": True,  # Expand sidebar by default
    
    # Custom icons
    "icons": {
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "payments.Payment": "fas fa-credit-card",
        "products.Product": "fas fa-box",
        "products.Category": "fas fa-tags",
    },
    
    # Theme options
    "theme": "dark",  # dark/light
}