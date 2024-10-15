from django.urls import re_path
from .consumers import EmailStatusConsumer

websocket_urlpatterns = [
    re_path(r'ws/email-status/', EmailStatusConsumer.as_asgi()),  # Define the WebSocket route
]
