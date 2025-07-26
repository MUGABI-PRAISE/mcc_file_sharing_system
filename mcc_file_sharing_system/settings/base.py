# mcc_file_sharing_system/settings/base.py

"""
BASE SETTINGS FILE
-------------------
This file contains the core settings that are shared across ALL environments
(development, production, staging, etc.). Environment-specific overrides will 
be applied in development.py or production.py.

We are using `python-decouple` to read from the `.env` file, which keeps secrets 
and environment-specific values outside of version control.
"""

import os
from pathlib import Path
from datetime import timedelta
from decouple import config  # Reads variables from `.env`

import cloudinary

cloudinary.config( 
  cloud_name = config('CLOUDINARY_CLOUD_NAME'),
  api_key = config('CLOUDINARY_API_KEY'),
  api_secret = config('CLOUDINARY_API_SECRET')
)

# ---------------------------------------------------------------------
# BASE DIRECTORY
# ---------------------------------------------------------------------
# BASE_DIR points to the project root. This makes it easy to define paths.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------
# SECURITY & DEBUG
# ---------------------------------------------------------------------
# SECRET_KEY is a required setting for cryptographic signing.
# DO NOT hardcode secrets in production; instead, set them in `.env`.
SECRET_KEY = config('SECRET_KEY', default='insecure-dev-key')

# DEBUG should always be False in production. We set a default (False)
# and override it in development.py.
DEBUG = config('DEBUG', default=False, cast=bool)

# ---------------------------------------------------------------------
# HOSTS & CORS
# ---------------------------------------------------------------------
# ALLOWED_HOSTS defines which domains can serve the Django app.
# Default: local development hosts.
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# CORS_ALLOWED_ORIGINS defines which frontends (origins) can make cross-origin requests.
# Default: React dev server at localhost:3000
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# ---------------------------------------------------------------------
# INSTALLED APPS
# ---------------------------------------------------------------------
INSTALLED_APPS = [
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Project apps
    'filesharing',

    # Third-party apps
    'corsheaders',  # For handling Cross-Origin Resource Sharing
    'rest_framework',  # Django REST Framework for APIs
    'cloudinary',  # Cloudinary integration
    'cloudinary_storage',  # Cloudinary storage backend
]

# ---------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # Whitenoise allows serving static files without an external server (used in prod)
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    # Handle cross-origin requests (must be before CommonMiddleware)
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ---------------------------------------------------------------------
# DATABASES
# ---------------------------------------------------------------------
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# ---------------------------------------------------------------------
# URLS & TEMPLATES
# ---------------------------------------------------------------------
ROOT_URLCONF = 'mcc_file_sharing_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # You can add global template directories here
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

WSGI_APPLICATION = 'mcc_file_sharing_system.wsgi.application'

# ---------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Kampala'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Location where static files are collected (for prod)

# ---------------------------------------------------------------------
# CUSTOM USER MODEL
# ---------------------------------------------------------------------
AUTH_USER_MODEL = 'filesharing.User'

# ---------------------------------------------------------------------
# REST FRAMEWORK CONFIGURATION
# ---------------------------------------------------------------------
REST_FRAMEWORK = {
    # Support both JWT and session-based authentication
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

# ---------------------------------------------------------------------
# SIMPLE JWT CONFIGURATION
# ---------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=1),   # Short lifetime for access tokens
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),     # Longer lifetime for refresh tokens
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
}

# ---------------------------------------------------------------------
# SECURITY HEADERS
# ---------------------------------------------------------------------
X_FRAME_OPTIONS = 'ALLOWALL'

# ---------------------------------------------------------------------
# CLOUDINARY CONFIGURATION (for file storage)
# ---------------------------------------------------------------------
# CLOUDINARY_STORAGE = {
#     'CLOUD_NAME': 'de68hyatv',
#     'API_KEY': '953861594452353',
#     'API_SECRET': 'ad6RUR6syKZWa7G0gIUVkU2Nnj4',
# }

# DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
