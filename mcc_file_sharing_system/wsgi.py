"""
WSGI config for mcc_file_sharing_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise # serving static files

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mcc_file_sharing_system.settings')

application = get_wsgi_application()
# setting whitenoise to serve static files. 

application = WhiteNoise(application, root=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles')) # move one level up to find the staticfiles folder,, relative to where the wsgi.py is currently

