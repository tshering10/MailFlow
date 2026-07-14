# emails/views.py
from rest_framework import viewsets, permissions
from .models import EmailSchedule
from .serializers import EmailScheduleSerializer

class EmailScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = EmailScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmailSchedule.objects.filter(created_by=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)