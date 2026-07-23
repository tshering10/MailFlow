# MailFlow

A background email scheduling platform built to learn Celery, Redis, Celery Beat, and background task processing in a real full-stack application — with a final integration step bridging into Django Channels for live status updates.

> **Status:** v1 — Core scheduling, retry, cancel, resend, WebSocket live-updates, user activity logging, and OAuth are working.

---

## Tech Stack

**Backend**
- Django 4.2 + Django REST Framework (DRF)
- PostgreSQL
- Redis (Message broker & Cache)
- Celery + Celery Beat (Background & scheduled tasks)
- Simple JWT & django-allauth (Authentication & Google OAuth)
- Django Channels (WebSockets for real-time email status updates)
- Daphne (ASGI server) & WhiteNoise (Static files)

**Frontend**
- React (To be built)

**Infra**
- Docker + Docker Compose

---

## Real-Time Workflow

- Creating an email schedule queues a Celery task and broadcasts a `QUEUED` websocket update.
- Cancelling a schedule revokes the task when possible, updates the database, and broadcasts `CANCELLED`.
- Resending an email re-queues the task and broadcasts `QUEUED` again.
- The Celery task broadcasts `PROCESSING`, `SENT`, and `FAILED` updates as the email moves through the async flow.

---

## API Endpoints

### Authentication (Users)
- `POST /api/users/register/` - Register a new user.
- `POST /api/users/login/` - Login (Email or Username) to obtain JWT access and refresh tokens.
- `POST /api/users/google/` - Login via Google OAuth (Frontend-first flow).
- `POST /api/users/logout/` - Logout (Blacklists the refresh token).
- `POST /api/users/token/refresh/` - Refresh the JWT access token.
- `GET /api/users/me/` - Retrieve the currently authenticated user's profile.
- `GET /api/users/activity/` - Retrieve paginated user activity logs (Audit trail).

### Email Scheduling
- `GET /api/emails/` - List all scheduled emails for the authenticated user (Supports Pagination, Filtering by status, Search, and Ordering).
- `POST /api/emails/` - Create a new email schedule.
- `GET /api/emails/{id}/` - Retrieve a specific email schedule.
- `PUT / PATCH /api/emails/{id}/` - Update an email schedule.
- `DELETE /api/emails/{id}/` - Delete an email schedule.
- `POST /api/emails/{id}/cancel/` - Cancel a pending or queued email schedule.
- `POST /api/emails/{id}/resend/` - Resend or retry a previously scheduled email.

### System
- `GET /api/health/` - Health check endpoint verifying DB and Redis status.

---

## WebSocket Endpoints

### Real-Time Status Updates
- `ws://<host>/ws/emails/?token=<jwt_token>` - Connect to receive real-time email status updates via Django Channels. Authenticated securely via JWT.

---

## Verified Backend Coverage

- Email schedule creation & execution via Celery.
- Cancel action with task revoke + WebSocket update.
- Resend action with WebSocket update.
- User activity logging (CREATED, CANCELLED, RESENT, DELETED).
- Secure JWT authentication, blacklisting, and Google SSO.
- Pagination, Searching, and Filtering on DRF views.
- WebSocket consumer connection and channel-layer broadcast delivery authenticated by custom JWT Middleware.
