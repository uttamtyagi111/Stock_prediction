# import django
# import os
# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.core.asgi import get_asgi_application
# from channels.auth import AuthMiddlewareStack
# from email_sender  import routing 

# import os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'email_automation.settings')

# # django.setup()

# django_asgi_app = get_asgi_application()

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(), 
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             routing.websocket_urlpatterns 
#         )
#     ),
# })


import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from email_sender import routing  # Ensure this matches your app structure

# Set the default Django settings module for the 'asgi' application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'email_automation.settings')

# Initialize the Django ASGI application early to populate AppRegistry
django_asgi_app = get_asgi_application()

# Define the ASGI application with HTTP and WebSocket protocols
application = ProtocolTypeRouter({
    # HTTP protocol handling
    "http": django_asgi_app,
    # WebSocket protocol handling
    "websocket": AllowedHostsOriginValidator(  # Restricts WebSocket connections to allowed hosts
        AuthMiddlewareStack(  # Adds authentication middleware for WebSocket connections
            URLRouter(
                routing.websocket_urlpatterns  # Connects WebSocket routes
            )
        )
    ),
})

