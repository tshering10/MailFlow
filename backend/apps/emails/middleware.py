from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model


User = get_user_model()


def _get_header(scope, name):
    headers = dict(scope.get('headers', []))
    return headers.get(name, b'').decode().strip()


def _extract_token_from_scope(scope):
    """
    Extract JWT access token from trusted handshake sources.
    Priority:
    1) HttpOnly cookie (mailflow-auth)
    2) Authorization header (Bearer <token>)
    3) Sec-WebSocket-Protocol token formats for browser clients
    """
    cookie_header = _get_header(scope, b'cookie')
    if cookie_header:
        for part in cookie_header.split(';'):
            key, sep, value = part.strip().partition('=')
            if sep and key == 'mailflow-auth' and value:
                return value

    auth_header = _get_header(scope, b'authorization')
    if auth_header.lower().startswith('bearer '):
        token = auth_header[7:].strip()
        if token:
            return token

    protocols = _get_header(scope, b'sec-websocket-protocol')
    if protocols:
        parts = [p.strip() for p in protocols.split(',') if p.strip()]
        if len(parts) == 2 and parts[0].lower() in {'bearer', 'jwt', 'token'}:
            return parts[1]

    return None


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
    from cookie, Authorization header, or WebSocket subprotocol.
    """

    async def __call__(self, scope, receive, send):
        token_key = _extract_token_from_scope(scope)

        # Set the authenticated user on the scope
        if token_key:
            scope['user'] = await get_user_from_token(token_key)
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
