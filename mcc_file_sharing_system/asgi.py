"""
ASGI config for mcc_file_sharing_system project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""
'''
it has now been wrapped by daphne, an asgi server for websockets.
'''

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mcc_file_sharing_system.settings.development")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from filesharing.routing import websocket_urlpatterns
from filesharing.middleware import JWTAuthMiddleware # this will allow our jwt based authentication to talk with web sockets


# django asgi app is now wrapped.
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # AuthMiddlewareStack gives you session auth; we wrap it with our JWT middleware so
    # scope["user"] is populated for both cookie sessions and JWT tokens.
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})