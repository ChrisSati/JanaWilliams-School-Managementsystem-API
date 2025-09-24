# middleware.py
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from users.models import User  # adjust as needed
import jwt
from django.conf import settings

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        scope["user"] = AnonymousUser()

        if token:
            try:
                access_token = AccessToken(token)
                user_id = access_token["user_id"]
                user = await self.get_user(user_id)
                if user:
                    scope["user"] = user
            except Exception:
                pass

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None





# # middleware.py
# from urllib.parse import parse_qs
# # from channels.middleware.base import BaseMiddleware
# from channels.middleware import BaseMiddleware
# from django.contrib.auth.models import AnonymousUser
# from rest_framework_simplejwt.tokens import AccessToken
# from users.models import User  # adjust as needed
# import jwt
# from django.conf import settings

# class JWTAuthMiddleware(BaseMiddleware):
#     async def __call__(self, scope, receive, send):
#         query_string = scope.get("query_string", b"").decode()
#         query_params = parse_qs(query_string)
#         token = query_params.get("token", [None])[0]

#         scope["user"] = AnonymousUser()

#         if token:
#             try:
#                 access_token = AccessToken(token)
#                 user_id = access_token["user_id"]
#                 user = await self.get_user(user_id)
#                 if user:
#                     scope["user"] = user
#             except Exception:
#                 pass

#         return await super().__call__(scope, receive, send)

#     @database_sync_to_async
#     def get_user(self, user_id):
#         try:
#             return User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return None
