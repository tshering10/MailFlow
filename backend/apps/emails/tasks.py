from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from .models import EmailSchedule, TaskLog, Status
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notify_user(user_id, email_id, status, sent_at=None, error_message=None):
    """
    Sends a real-time WebSocket notification to the user
    via the Channel Layer (Redis) group for this specific user.
    """
    print("=" * 60)
    print("notify_user() called")
    print(f"user_id: {user_id}")
    print(f"email_id: {email_id}")
    print(f"status: {status}")
    print("=" * 60)

    channel_layer = get_channel_layer()
    print("Layer:", channel_layer)

    group_name = f"User_{user_id}_emails"
    print("Group:", group_name)

    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "email_status_update",
                "email_id": str(email_id),
                "status": status,
                "sent_at": str(sent_at) if sent_at else None,
                "error_message": error_message,
            },
        )

        print("group_send SUCCESS")

    except Exception as e:
        print("group_send FAILED")
        print(repr(e))

    print("=" * 60)

@shared_task(bind=True, max_retries=3)
def send_email_task(self, email_id):

    print("=" * 60)
    print("TASK STARTED")
    print(email_id)
    print("=" * 60)
    
    try:
        email = EmailSchedule.objects.get(id=email_id)
    except EmailSchedule.DoesNotExist:
        return f"Email {email_id} not found."

    # If the user cancelled the email schedule, abort sending
    if email.status == Status.CANCELLED:
        return f"Email {email_id} was cancelled."

    # Create task log entry
    log = TaskLog.objects.create(
        task_name="send_email_task",
        email=email,
        status="RUNNING",
        started_at=timezone.now(),
        retry_count=self.request.retries
    )

    # Update database record to PROCESSING
    email.status = Status.PROCESSING
    email.save(update_fields=['status'])
    notify_user(email.created_by_id, email_id, Status.PROCESSING)

    try:
        # Send email using configured email backend
        send_mail(
            subject=email.subject,
            message=email.body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mailflow.com'),
            recipient_list=[email.recipient],
            fail_silently=False,
        )
        
        # Mark email schedule as SENT
        now = timezone.now()
        email.status = Status.SENT
        email.sent_at = now
        email.save(update_fields=['status', 'sent_at'])
        
        # Update log
        log.status = "SUCCESS"
        log.finished_at = now
        log.save(update_fields=['status', 'finished_at'])
        
        # notify user of success via websocket
        notify_user(email.created_by_id, email_id, Status.SENT, sent_at=now)

        return f"Email {email_id} sent successfully."

    except Exception as exc:
        # Check if we can retry the execution
        if self.request.retries < self.max_retries:
            log.status = "RETRYING"
            log.error = str(exc)
            log.finished_at = timezone.now()
            log.save(update_fields=['status', 'error', 'finished_at'])
            
            # Retry after 10 seconds
            raise self.retry(exc=exc, countdown=10)
        
        # Out of retries, mark as FAILED
        now = timezone.now()
        email.status = Status.FAILED
        email.error_message = str(exc)
        email.save(update_fields=['status', 'error_message'])
        
        log.status = "FAILED"
        log.error = str(exc)
        log.finished_at = now
        log.save(update_fields=['status', 'error', 'finished_at'])
        
        notify_user(email.created_by_id, email_id, Status.FAILED, error_message=str(exc))
        return f"Email {email_id} failed: {str(exc)}"

