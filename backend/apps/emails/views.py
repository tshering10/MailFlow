# emails/views.py
from .tasks import send_email_task
from rest_framework import viewsets, permissions
from .models import EmailSchedule, Status
from .serializers import EmailScheduleSerializer

class EmailScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = EmailScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmailSchedule.objects.filter(created_by=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        email = serializer.save(created_by=self.request.user)

        # trigger enqueuing of the celery task with eta
        task = send_email_task.apply_async(
            args=[str(email.id)],
            eta=email.scheduled_at
        )

          #Save celery task ID and update status to QUEUED
        email.celery_task_id = task.id
        email.status = Status.QUEUED
        email.save(update_fields=['celery_task_id', 'status'])