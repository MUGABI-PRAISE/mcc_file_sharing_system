from django.urls import path
from .consumers import NotificationConsumer, ChatConsumer

# No parameters in the URL. We infer office/user from scope["user"].
websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    path("ws/chat/", ChatConsumer.as_asgi()), 
]
