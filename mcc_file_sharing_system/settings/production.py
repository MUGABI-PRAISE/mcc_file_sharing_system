# mcc_file_sharing_system/settings/production.py

"""
PRODUCTION SETTINGS
---------------------
This file contains overrides for the production environment.
These settings prioritize security and performance.
"""

from .base import *

# DEBUG must be False in production for security reasons
DEBUG = False

# ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS MUST be set in .env in production
# (base.py will read them from environment variables)

# ---------------------------------------------------------------------
# SECURITY SETTINGS
# ---------------------------------------------------------------------
# Redirect all HTTP requests to HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False

# Make cookies secure (only sent over HTTPS)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Enable HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 3600  # Browsers will only use HTTPS for 1 hour (adjust as needed)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------------------
# STATIC FILES STORAGE
# ---------------------------------------------------------------------
# Use manifest-based storage for cache busting in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
