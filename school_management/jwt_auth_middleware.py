# users/middleware.py
import logging
from urllib.parse import parse_qs

from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user_from_token(raw_token: str):
    """
    Validate a JWT and return a user (or AnonymousUser).
    """
    jwt_auth = JWTAuthentication()
    try:
        validated = jwt_auth.get_validated_token(raw_token)
        return jwt_auth.get_user(validated)
    except (InvalidToken, AuthenticationFailed) as exc:
        logger.warning(f"JWT validation error in WebSocket: {exc}")
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    """
    Extract ?token=<JWT> from the query-string, validate it with DRF SimpleJWT,
    and attach the user to scope['user'].
    """
    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = query.get("token", [None])[0]

        scope["user"] = (
            await get_user_from_token(token) if token else AnonymousUser()
        )

        return await super().__call__(scope, receive, send)
