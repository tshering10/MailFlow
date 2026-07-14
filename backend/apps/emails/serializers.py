from rest_framework import serializers
from .models import EmailSchedule, TaskLog

class EmailScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSchedule
        fields = ['id', 'recipient', 'subject', 'body', 'status', 'scheduled_at', 'sent_at', 'error_message', 'celery_task_id', 'created_at']
        read_only_fields = ['status', 'error_message', 'celery_task_id', 'sent_at', 'created_at']
