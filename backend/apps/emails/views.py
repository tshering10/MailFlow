# emails/views.py
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import EmailSchedule, Status
from .serializers import EmailScheduleSerializer
from celery import current_app
from .tasks import send_email_task, notify_user

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

        # Notify connected websocket clients that the email has been scheduled
        notify_user(email.created_by_id, email.id, Status.QUEUED)

    def perform_destroy(self, instance):
        """
        Cleans up background resources when a schedule is deleted.
        If the email is still pending execution, revoke it from Celery.
        """
        # If the email is active (PENDING/QUEUED) and has a task ID, revoke it from Celery queue
        if instance.status in [Status.PENDING, Status.QUEUED] and instance.celery_task_id:
            current_app.control.revoke(instance.celery_task_id, terminate=True)

        # Delete the email record from the database
        instance.delete()

    @action(detail=True, methods=['POST'])
    def cancel(self, request, pk=None):
        email = self.get_object()

           # Only allow cancellation if the email is not already processing, sent, or failed
        if email.status not in [Status.PENDING, Status.QUEUED]:
            return Response(
                {"error": f"Cannot cancel an email that is already {email.status.lower()}. "},
                status=status.HTTP_400_BAD_REQUEST
            )
        
           # Revoke the background task from the Celery broker if it exists
        if email.celery_task_id:
            current_app.control.revoke(email.celery_task_id, terminate=True)

        # Always update status to CANCELLED in DB
        email.status = Status.CANCELLED
        email.save(update_fields=['status'])

        # Notify connected websocket clients immediately
        notify_user(email.created_by_id, email.id, Status.CANCELLED)

        return Response(
            {"message": "Email schedule has been cancelled successfully."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'])
    def resend(self, request, pk=None):
        # custom endpoints to retry or resend an email
        email = self.get_object()

        if email.status in [Status.PENDING, Status.QUEUED, Status.PROCESSING]:
            return Response(
                {"error": f"Cannot resend an email that is currently in {email.status.lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        new_scheduled_at = request.data.get('scheduled_at')
        if new_scheduled_at:
            email.scheduled_at = new_scheduled_at
            task = send_email_task.apply_async(
                args=[str(email.id)],
                eta=email.scheduled_at
            )
        else:
            email.scheduled_at = timezone.now()
            task = send_email_task.delay(str(email.id))

         #reset status for retry
        email.status = Status.QUEUED
        email.celery_task_id = task.id
        email.sent_at = None
        email.error_message = None
        email.save(update_fields=['status', 'celery_task_id', 'scheduled_at', 'sent_at', 'error_message'])

        # Notify connected websocket clients that the email has been re-queued
        notify_user(email.created_by_id, email.id, Status.QUEUED)

        #return updated email schedule object
        serializer = self.get_serializer(email)
        return Response(serializer.data, status=status.HTTP_200_OK)   