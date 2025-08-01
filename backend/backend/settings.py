# backend/settings.py
import os
from pathlib import Path
from decouple import config
from datetime import timedelta

# Debug: Print a variable to confirm it’s being read
print("DATABASE_NAME:", config('DATABASE_NAME'))

BASE_DIR = Path(__file__).resolve().parent.parent 

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['proyecto-final-desarrollo-de-software-i-cg29.onrender.com',
    '127.0.0.1',
    'localhost',]

    



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'tickets',
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
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Configuración de logging para depuración
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

STATIC_URL = 'static/'
SECRET_KEY = config('SECRET_KEY')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Para desarrollo
    "https://frontend-ecru-nine-84.vercel.app",  # Ajusta con tu dominio exacto de Vercel
]
CORS_ALLOW_CREDENTIALS = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

AUTH_USER_MODEL = 'tickets.Usuario'

# Configuración de correo
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sitema.atenciondsi@gmail.com'
EMAIL_HOST_PASSWORD = 'ilmq sfmv bjnb fkiz'  # Cambia si usas contraseña de app
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
#Estas credenciales van en el .env Tanto credenciales y bases de datos
#Django enviroment

# Configuración de REST Framework y JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Cambia a 1 hora
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),  # 1 día para el refresh
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'BLACKLIST_AFTER_ROTATION': True,
}

LOGIN_RATE_LIMIT = '2/m'  # Máximo 5 intentos por minuto
LOGIN_FAILS_LIMIT = 2     # Se permiten 5 fallos antes de bloquear
LOGIN_FAILS_TIMEOUT = 60 # Bloqueo durante 5 minutos (300 segundos)

# Configuración de caché para almacenar intentos fallidos
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',  # Identificador único de caché
    }
}

if not DEBUG:
    ALLOWED_HOSTS = ['proyecto-final-desarrollo-de-software-i-cg29.onrender.com',
    '127.0.0.1',
    'localhost',]
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

    X_FRAME_OPTIONS = 'DENY'

    # Seguridad en cabeceras
    
else:
    # Solo en desarrollo
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']



