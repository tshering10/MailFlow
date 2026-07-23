# MailFlow Security Documentation

This document outlines the security measures and best practices implemented in the MailFlow backend to ensure data integrity, prevent unauthorized access, and protect against common web vulnerabilities.

## 1. Authentication & Authorization

### JWT (JSON Web Tokens)
- **Implementation**: Used `rest_framework_simplejwt` for stateless authentication.
- **Lifespans**: Access tokens are short-lived (e.g., 60 minutes). Refresh tokens are used to obtain new access tokens.
- **Token Blacklisting**: Implemented token blacklisting on logout. When a user logs out, their refresh token is added to a database blacklist, immediately preventing it from being used to generate new access tokens.

### Google OAuth (SSO)
- **Implementation**: Used `dj-rest-auth` and `django-allauth` for seamless Google login.
- **Architecture**: Employs a Frontend-first OAuth flow. The React frontend obtains the access token/code directly from Google and securely exchanges it with the Django backend for a JWT, keeping the backend isolated from the initial OAuth redirection complexities.

### WebSocket Authentication
- **Implementation**: Custom `JWTAuthMiddleware` intercepting connections to `/ws/emails/`.
- **Validation**: Extracts the JWT from trusted handshake sources in priority order:
  1. **HttpOnly Cookie**: Checks for the `mailflow-auth` cookie.
  2. **Authorization Header**: Checks for a standard `Bearer <token>` header.
  3. **WebSocket Subprotocol**: Checks the `Sec-WebSocket-Protocol` header for token formats sent by browser clients.
  
  The token is validated against the database, and the authenticated `User` object is attached to the Channels scope, preventing unauthorized WebSocket connections.

## 2. Rate Limiting (Throttling)

To protect the API from brute-force attacks and abuse, strict rate limiting is applied globally and on sensitive endpoints using DRF's throttling classes:

- **Global Anonymous Users**: 100 requests per day.
- **Global Authenticated Users**: 1000 requests per day.

## 3. Web Security Headers & Cookies

When `DEBUG=False` (Production mode), Django enforces several critical security settings:

- **Secure Cookies**: Both Session (`SESSION_COOKIE_SECURE`) and CSRF (`CSRF_COOKIE_SECURE`) cookies are marked as `Secure`, meaning they will only be sent over HTTPS.
- **SSL Redirect**: `SECURE_SSL_REDIRECT` forces all HTTP traffic to HTTPS.
- **Content Type Sniffing**: `SECURE_CONTENT_TYPE_NOSNIFF` prevents browsers from guessing the content type, mitigating certain types of XSS attacks.
- **XSS Filter**: `SECURE_BROWSER_XSS_FILTER` enables the browser's built-in XSS protection.

## 4. Cross-Origin Resource Sharing (CORS)

- **Implementation**: `django-cors-headers` is configured to only allow requests from trusted origins.
- **Dynamic Configuration**: `CORS_ALLOWED_ORIGINS` is loaded directly from environment variables, ensuring that only the specific production frontend domains are whitelisted, preventing unauthorized sites from making API requests to the backend.

## 5. Environment Variables & Secrets Management

- **No Hardcoded Secrets**: Sensitive credentials such as `SECRET_KEY`, Database credentials, and Redis URLs are strictly loaded via `os.environ.get()` and managed using a `.env` file (or docker-compose environment variables).
- **DEBUG Mode**: `DEBUG` is strictly managed via environment variables, ensuring it is always `False` in production to prevent stack trace leaks.

## 6. Audit Logging

- **ActivityLog**: Every sensitive user action (Creating, Cancelling, Resending, or Deleting an email schedule) is recorded in the `ActivityLog` table. This provides a clear, immutable audit trail for user behavior and system state changes.
