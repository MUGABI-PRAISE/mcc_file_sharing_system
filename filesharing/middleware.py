import urllib.parse
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

User = get_user_model()

class JWTAuthMiddleware:
    """
    Custom JWT middleware for Django Channels.
    """

    def __init__(self, inner):
        self.inner = inner
        self.jwt_auth = JWTAuthentication()

    async def __call__(self, scope, receive, send):
        # If session auth already set a user, keep it
        user = scope.get("user", AnonymousUser())
        if user.is_authenticated:
            return await self.inner(scope, receive, send)

        # Otherwise, look for ?token=<JWT>
        query_string = scope.get("query_string", b"").decode()
        params = urllib.parse.parse_qs(query_string)
        token_list = params.get("token", [])

        if token_list:
            token = token_list[0]
            user = await self._authenticate_token(token)
            scope["user"] = user or AnonymousUser()

        # Pass control to next ASGI application
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def _authenticate_token(self, raw_token):
        try:
            validated_token = self.jwt_auth.get_validated_token(raw_token)
            user = self.jwt_auth.get_user(validated_token)
            return user
        except Exception:
            return None
