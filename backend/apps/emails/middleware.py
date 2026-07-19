from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    """
    Validates the JWT access token and returns the corresponding User object.
    Returns AnonymousUser if the token is invalid or expired.
    """
    try:
        # Decode and validate the token
        token = AccessToken(token_key)
        user_id = token['user_id']
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom WebSocket middleware that authenticates users via JWT tokens
    passed as a query parameter: ws://localhost:8000/ws/emails/?token=<access_token>
    """

    async def __call__(self, scope, receive, send):
        # Parse the query string from the WebSocket URL
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)

        # Extract the token value from the query parameters
        token_list = query_params.get('token', [None])
        token_key = token_list[0]

        # Set the authenticated user on the scope
        if token_key:
            scope['user'] = await get_user_from_token(token_key)
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
