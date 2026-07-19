# MailFlow

A background email scheduling platform built to learn Celery, Redis, Celery Beat, and background task processing in a real full-stack application — with a final integration step bridging into Django Channels for live status updates.

> **Status:** v1 — core scheduling, retry, cancel, resend, and WebSocket live-update flows are working.

---

## Tech Stack

**Backend**
- Django + Django REST Framework
- PostgreSQL
- Redis (message broker)
- Celery + Celery Beat (background & scheduled tasks)
- Simple JWT (authentication)
- Django Channels for real-time email status updates

**Frontend**
- React

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
- `POST /api/users/login/` - Login to obtain JWT access and refresh tokens.
- `POST /api/users/token/refresh/` - Refresh the JWT access token.
- `GET /api/users/me/` - Retrieve the currently authenticated user's profile.

### Email Scheduling
- `GET /api/emails/` - List all scheduled emails for the authenticated user.
- `POST /api/emails/` - Create a new email schedule.
- `GET /api/emails/{id}/` - Retrieve a specific email schedule.
- `PUT / PATCH /api/emails/{id}/` - Update an email schedule.
- `DELETE /api/emails/{id}/` - Delete an email schedule.
- `POST /api/emails/{id}/cancel/` - Cancel a pending or queued email schedule.
- `POST /api/emails/{id}/resend/` - Resend or retry a previously scheduled email.

---

## WebSocket Endpoints

### Real-Time Status Updates
- `ws://<host>/ws/emails/` - Connect to receive real-time email status updates via Django Channels.

---

## Verified Backend Coverage

- Email schedule creation
- Cancel action with task revoke + websocket update
- Resend action with websocket update
- WebSocket consumer connection and channel-layer broadcast delivery
