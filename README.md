# MailFlow

A background email scheduling platform built to learn Celery, Redis, Celery Beat, and background task processing in a real full-stack application — with a final integration step bridging into Django Channels for live status updates.

> **Status:** v1 — core scheduling, retry, and cancel flows working. WebSocket live-update bridge and stretch goals are in progress.

---

## Tech Stack

**Backend**
- Django + Django REST Framework
- PostgreSQL
- Redis (message broker)
- Celery + Celery Beat (background & scheduled tasks)
- Simple JWT (authentication)

**Frontend**
- React

**Infra**
- Docker + Docker Compose

---

