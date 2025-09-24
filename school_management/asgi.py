# ziongrove/asgi.py
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_management.settings")
django.setup()

from users.middleware import JwtAuthMiddleware
import chat.routing

# WebSocket routes (only chat)
websocket_urlpatterns = chat.routing.websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JwtAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})




# """
# ASGI config for school_management project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
# """

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_management.settings")

# application = get_asgi_application()
