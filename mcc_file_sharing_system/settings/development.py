# mcc_file_sharing_system/settings/development.py

"""
DEVELOPMENT SETTINGS
---------------------
This file contains overrides for the development environment.
These settings prioritize simplicity and debugging convenience over security.
"""

from .base import *

# Enable debug mode so Django shows detailed error pages
DEBUG = True

# ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS already have sensible defaults in base.py.
# You can override them here if you need to add more.
# ALLOWED_HOSTS = ['localhost', '127.0.0.1']
# CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# ---------------------------------------------------------------------
# SECURITY SETTINGS (DISABLED FOR DEV)
# ---------------------------------------------------------------------
SECURE_SSL_REDIRECT = False  # Do not force HTTPS in dev
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Disable HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# ---------------------------------------------------------------------
# STATIC FILES STORAGE
# ---------------------------------------------------------------------
# Use simpler static file storage that doesn’t hash filenames (easier during dev)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
