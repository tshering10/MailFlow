from django.db import models
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

class Status(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    QUEUED = 'QUEUED', 'Queued'
    PROCESSING = 'PROCESSING', 'Processing'
    SENT = 'SENT', 'Sent'
    FAILED = 'FAILED', 'Failed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class EmailSchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="emails")

    def __str__(self):
        return f"{self.subject} -> {self.recipient} [{self.status}]"


class TaskLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_name = models.CharField(max_length=255)
    email = models.ForeignKey(EmailSchedule, on_delete=models.CASCADE, related_name='logs', null=True)
    status = models.CharField(max_length=20)

    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    error = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.task_name} [{self.status}]"