import django
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from email_sender  import routing  # Replace with your app name

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'email_automation.settings')
django.setup()
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Django's ASGI application for HTTP
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns  # WebSocket routing
        )
    ),
})
