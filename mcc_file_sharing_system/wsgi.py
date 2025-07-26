"""
WSGI config for mcc_file_sharing_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mcc_file_sharing_system.settings')

application = get_wsgi_application()

# Only wrap WhiteNoise in production
from django.conf import settings
if not settings.DEBUG:
    from whitenoise import WhiteNoise
    application = WhiteNoise(application, root=settings.STATIC_ROOT)
