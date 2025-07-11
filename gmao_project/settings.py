"""
Django settings for gmao_project project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps tiers
    'rest_framework',
    'corsheaders',
    'django_filters',
    
    # Apps locales
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuration REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Configuration CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'gmao_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gmao_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
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
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login settings
LOGIN_URL = 'connexion'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'connexion'

GMAO_SETTINGS = {
    # Configuration mobile
    'MOBILE_API_VERSION': '1.0',
    'MOBILE_TOKEN_EXPIRY_DAYS': 30,
    'OFFLINE_SYNC_MAX_DAYS': 7,
    
    # Configuration médias
    'MAX_FILE_SIZE_MB': 50,
    'ALLOWED_IMAGE_TYPES': ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
    'ALLOWED_AUDIO_TYPES': ['mp3', 'wav', 'm4a', 'ogg'],
    'ALLOWED_VIDEO_TYPES': ['mp4', 'avi', 'mov', 'mkv', 'webm'],
    'ALLOWED_DOCUMENT_TYPES': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'],
    
    # Configuration QR codes
    'QR_CODE_SIZE': 200,
    'QR_CODE_BORDER': 4,
    'QR_CODE_VERSION': 1,
    
    # Configuration demandes de réparation
    'AUTO_ASSIGN_REPAIR_REQUESTS': False,
    'BLOCK_OT_COMPLETION_ON_PENDING_REPAIRS': True,
    'AUTO_GENERATE_REPAIR_NUMBERS': True,
    
    # Configuration notifications
    'ENABLE_PUSH_NOTIFICATIONS': True,
    'NOTIFICATION_RETENTION_DAYS': 30,
    
    # Configuration synchronisation
    'ENABLE_OFFLINE_MODE': True,
    'AUTO_SYNC_INTERVAL_MINUTES': 15,
    'BACKGROUND_SYNC_ENABLED': True,
}

# Configuration cache pour les performances
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 300,  # 5 minutes
        'KEY_PREFIX': 'gmao',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    },
    'mobile_sync': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'TIMEOUT': 3600,  # 1 heure
        'KEY_PREFIX': 'gmao_mobile',
    }
}

# Configuration de compression des médias
MEDIA_COMPRESSION = {
    'ENABLE_IMAGE_COMPRESSION': True,
    'IMAGE_QUALITY': 85,
    'MAX_IMAGE_RESOLUTION': (1920, 1080),
    'ENABLE_VIDEO_COMPRESSION': True,
    'VIDEO_QUALITY': 'medium',
}
