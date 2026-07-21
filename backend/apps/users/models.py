from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class ActivityAction(models.TextChoices):
    CREATED = "CREATED", "Created"
    UPDATED = "UPDATED", "Updated"
    QUEUED = "QUEUED", "Queued"
    PROCESSING = "PROCESSING", "Processing"
    SENT = "SENT", "Sent"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"
    RESENT = "RESENT", "Resent"
    DELETED = "DELETED", "Deleted"

class User(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class ActivityLog(models.Model):
    email = models.ForeignKey(
        'emails.EmailSchedule',
        on_delete=models.CASCADE,
        related_name="activities", null=True, blank=True
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="activities"
    )

    action = models.CharField(
        max_length=30,
        choices=ActivityAction.choices
    )
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        subject = self.email.subject if self.email else "No Subject"
        return f"{self.action} - {subject}"