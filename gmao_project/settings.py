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
                'core.context_processors.user_role_context',
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

# Configuration de la carte FTTH
# ===============================

# Région par défaut pour le centrage de la carte
# Options: 'france', 'paris', 'lyon', 'marseille'
GMAO_DEFAULT_REGION = 'france'

# Validation stricte des coordonnées (France métropolitaine + DOM-TOM)
# Si True, rejette les coordonnées hors de France
# Si False, accepte toutes les coordonnées GPS valides
GMAO_STRICT_COORDINATES = False
# Configuration du logging pour la carte
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/carte_ftth.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'core.views': {  # Remplacez 'core' par le nom de votre app
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configuration des assets
# =========================

# Nombre maximum d'assets à afficher sur la carte
GMAO_MAX_ASSETS_ON_MAP = 1000

# Rayon de recherche pour les assets proches (en mètres)
GMAO_NEARBY_ASSETS_RADIUS = 100

# Configuration de la recherche
# ==============================

# Nombre maximum de résultats de recherche
GMAO_MAX_SEARCH_RESULTS = 20

# Délai de recherche (en millisecondes)
GMAO_SEARCH_DELAY = 300

# Configuration des performances
# ===============================

# Utiliser la mise en cache pour les données de la carte
GMAO_USE_CACHE = True

# Durée de mise en cache (en secondes)
GMAO_CACHE_DURATION = 300  # 5 minutes

# Configuration de sécurité
# ==========================

# Limiter l'accès à la carte selon les rôles
GMAO_CARTE_ROLES_ALLOWED = ['ADMIN', 'MANAGER', 'TECHNICIEN']

# Configuration des coordonnées personnalisées
# =============================================

# Vous pouvez ajouter vos propres coordonnées par défaut
GMAO_CUSTOM_COORDINATES = {
    'siege_social': {'lat': 48.8566, 'lng': 2.3522},
    'depot_nord': {'lat': 50.6292, 'lng': 3.0573},
    'depot_sud': {'lat': 43.2965, 'lng': 5.3698},
    # Ajoutez vos propres coordonnées ici
}

# Configuration des couleurs pour les statuts
# ============================================

GMAO_STATUS_COLORS = {
    'en_service': '#10b981',      # Vert
    'en_panne': '#ef4444',        # Rouge
    'en_maintenance': '#f59e0b',  # Orange
    'hors_service': '#6b7280',    # Gris
    'planifie': '#3b82f6',        # Bleu
}

# Configuration des icônes par catégorie
# =======================================

GMAO_CATEGORY_ICONS = {
    'nro': 'fas fa-server',
    'pm': 'fas fa-network-wired',
    'pb': 'fas fa-cube',
    'pto': 'fas fa-home',
    'cable': 'fas fa-minus',
    'default': 'fas fa-circle',
}

# Configuration des alertes
# =========================

# Activer les alertes pour les coordonnées invalides
GMAO_ALERT_INVALID_COORDINATES = True

# Email pour les alertes de configuration
GMAO_ALERT_EMAIL = 'admin@votre-entreprise.com'

# Configuration de développement
# ==============================

# Activer le mode debug pour la carte (plus de logs)
GMAO_DEBUG_MODE = DEBUG

# Afficher les assets avec coordonnées invalides dans l'interface
GMAO_SHOW_INVALID_ASSETS = DEBUG

# Configuration des permissions
# =============================

# Permissions requises pour accéder à la carte
GMAO_CARTE_PERMISSIONS = [
    'core.view_asset',
    'core.view_carte',
]