# MailFlow Architecture Documentation

## Overview
MailFlow is a robust, asynchronous email scheduling and management platform. It allows users to schedule emails for future delivery, manage their email queues, and track activity logs. The system is designed to handle background processing reliably and provide real-time updates to the frontend.

## Technology Stack
- **Backend Framework**: Django 4.2 & Django REST Framework (DRF)
- **Database**: PostgreSQL
- **Asynchronous Task Queue**: Celery
- **Message Broker & Cache**: Redis
- **Real-time Communication**: Django Channels (WebSockets)
- **Authentication**: SimpleJWT & django-allauth (Google OAuth)
- **Server**: Daphne (ASGI) & WhiteNoise (Static Files)
- **Deployment**: Docker & Docker Compose

## System Components

### 1. Web Server (Daphne/Django)
Handles all incoming HTTP and WebSocket requests. It serves the REST API endpoints and manages real-time WebSocket connections.

### 2. PostgreSQL Database
The primary data store for the application. It holds all user information, email schedules, activity logs, and celery task logs.

### 3. Redis
Acts as the message broker for Celery (passing tasks from Django to Celery workers) and as the channel layer backend for Django Channels (broadcasting WebSocket messages).

### 4. Celery Worker
Runs in the background and constantly listens to Redis for new tasks. When an email's scheduled time arrives, the Celery worker executes the task (sending the email) and updates the database.

### 5. Celery Beat (Scheduler)
(Optional/Available) Used if periodic tasks are required (e.g., cleaning up old logs or retrying failed emails automatically).

## Data Models

### Users App (`apps.users`)
- **User**: Custom user model extending `AbstractUser`. Uses email as the unique identifier.
- **ActivityLog**: Tracks every significant action a user takes (CREATED, CANCELLED, RESENT, DELETED) to provide a full audit trail.

### Emails App (`apps.emails`)
- **EmailSchedule**: The core model representing an email to be sent. Contains recipient, subject, body, scheduled time, and its current status (PENDING, QUEUED, PROCESSING, SENT, FAILED, CANCELLED).
- **TaskLog**: Records the execution details of Celery tasks, including retries and error messages.

## Key Workflows

### 1. Email Scheduling Flow
1. User submits a POST request to `/api/emails/` with email details and a `scheduled_at` time.
2. Django saves the `EmailSchedule` record with `PENDING` status.
3. Django calls `send_email_task.apply_async(eta=scheduled_at)`.
4. The task is queued in Redis, and Django updates the status to `QUEUED`.
5. Django creates an `ActivityLog` record.
6. Django broadcasts a WebSocket message to the user that the email is queued.

### 2. Email Execution Flow
1. When `scheduled_at` arrives, the Celery worker picks up the task from Redis.
2. Celery updates the status to `PROCESSING`.
3. Celery attempts to send the email using Django's email backend.
4. On success: Status becomes `SENT`, `sent_at` is updated.
5. On failure: Status becomes `FAILED`, `error_message` is recorded.
6. Celery creates a `TaskLog` and broadcasts a WebSocket message with the final status.
