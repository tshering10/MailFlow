from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from .models import EmailSchedule, TaskLog, Status

@shared_task(bind=True, max_retries=3)
def send_email_task(self, email_id):
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
        
        return f"Email {email_id} failed: {str(exc)}"
