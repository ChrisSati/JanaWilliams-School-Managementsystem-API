from django.utils import timezone
# jwt_auth_middleware.py
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode, DecodeError
from django.conf import settings
import logging

from .models import User  # direct import here

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token")

        if not token:
            scope['user'] = AnonymousUser()
            return await super().__call__(scope, receive, send)

        try:
            UntypedToken(token[0])
            decoded_data = jwt_decode(token[0], settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get("user_id")
            if user_id is None:
                raise KeyError("user_id not found in token")
            user = await get_user(user_id)
            scope['user'] = user
        except (InvalidToken, TokenError, KeyError, DecodeError) as e:
            logger.warning(f"WebSocket JWT token error: {e}")
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)


class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Safely check if 'user' attribute exists on request and user is authenticated
        if hasattr(request, "user") and request.user.is_authenticated:
            request.user.last_seen = timezone.now()
            request.user.save(update_fields=['last_seen'])

        return response