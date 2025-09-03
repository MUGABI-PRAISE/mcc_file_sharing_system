# mcc_file_sharing_system/settings/__init__.py

"""
DYNAMIC SETTINGS LOADER
-----------------------
This file decides which settings file (development or production) Django should use
based on the DJANGO_ENV environment variable.

- If DJANGO_ENV is 'production' → load production.py
- Otherwise → load development.py (default)
"""

import os

DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development').lower()

if DJANGO_ENV == 'production':
    from .production import *
else:
    from .development import *
