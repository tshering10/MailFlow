from datetime import timedelta
from unittest.mock import MagicMock, patch

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from config.asgi import application
from .models import EmailSchedule, Status


User = get_user_model()


@override_settings(
    CHANNEL_LAYERS={
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }
)
class EmailWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='password123',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _scheduled_payload(self):
        return {
            'recipient': 'receiver@example.com',
            'subject': 'Test email',
            'body': 'Body text',
            'scheduled_at': (timezone.now() + timedelta(hours=1)).isoformat(),
        }

    def test_create_email_schedules_task_and_broadcasts_queued(self):
        with patch('apps.emails.views.send_email_task.apply_async') as mock_apply_async, \
            patch('apps.emails.views.notify_user') as mock_notify:
            mock_apply_async.return_value = MagicMock(id='task-123')

            response = self.client.post(reverse('emails-list'), self._scheduled_payload(), format='json')

        self.assertEqual(response.status_code, 201)
        email = EmailSchedule.objects.get()
        self.assertEqual(email.status, Status.QUEUED)
        self.assertEqual(email.celery_task_id, 'task-123')
        mock_apply_async.assert_called_once()
        mock_notify.assert_called_once_with(self.user.id, email.id, Status.QUEUED)

    def test_cancel_email_revokes_task_updates_status_and_broadcasts(self):
        email = EmailSchedule.objects.create(
            created_by=self.user,
            recipient='receiver@example.com',
            subject='Test email',
            body='Body text',
            scheduled_at=timezone.now() + timedelta(hours=1),
            status=Status.QUEUED,
            celery_task_id='task-456',
        )

        with patch('apps.emails.views.current_app.control.revoke') as mock_revoke, \
            patch('apps.emails.views.notify_user') as mock_notify:
            response = self.client.post(reverse('emails-cancel', args=[email.id]), format='json')

        self.assertEqual(response.status_code, 200)
        email.refresh_from_db()
        self.assertEqual(email.status, Status.CANCELLED)
        mock_revoke.assert_called_once_with('task-456', terminate=True)
        mock_notify.assert_called_once_with(self.user.id, email.id, Status.CANCELLED)

    def test_resend_email_queues_again_and_broadcasts(self):
        email = EmailSchedule.objects.create(
            created_by=self.user,
            recipient='receiver@example.com',
            subject='Test email',
            body='Body text',
            scheduled_at=timezone.now() - timedelta(days=1),
            status=Status.FAILED,
            celery_task_id='old-task',
            error_message='previous failure',
        )

        with patch('apps.emails.views.send_email_task.delay') as mock_delay, \
            patch('apps.emails.views.notify_user') as mock_notify:
            mock_delay.return_value = MagicMock(id='task-789')

            response = self.client.post(
                reverse('emails-resend', args=[email.id]),
                data={},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        email.refresh_from_db()
        self.assertEqual(email.status, Status.QUEUED)
        self.assertEqual(email.celery_task_id, 'task-789')
        self.assertIsNone(email.sent_at)
        self.assertIsNone(email.error_message)
        mock_delay.assert_called_once_with(str(email.id))
        mock_notify.assert_called_once_with(self.user.id, email.id, Status.QUEUED)

    def test_websocket_connect_and_receive_broadcast(self):
        token = str(RefreshToken.for_user(self.user).access_token)
        email = EmailSchedule.objects.create(
            created_by=self.user,
            recipient='receiver@example.com',
            subject='Websocket email',
            body='Body text',
            scheduled_at=timezone.now() + timedelta(hours=1),
            status=Status.QUEUED,
            celery_task_id='task-999',
        )

        async def websocket_flow():
            communicator = WebsocketCommunicator(
                application,
                f'/ws/emails/?token={token}',
            )

            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            connection_payload = await communicator.receive_json_from()
            self.assertEqual(connection_payload['type'], 'connection_established')

            await get_channel_layer().group_send(
                f'User_{self.user.id}_emails',
                {
                    'type': 'email_status_update',
                    'email_id': str(email.id),
                    'status': Status.QUEUED,
                    'sent_at': None,
                    'error_message': None,
                },
            )

            broadcast_payload = await communicator.receive_json_from()
            self.assertEqual(broadcast_payload['type'], 'email_status_update')
            self.assertEqual(broadcast_payload['email_id'], str(email.id))
            self.assertEqual(broadcast_payload['status'], Status.QUEUED)

            await communicator.disconnect()

        async_to_sync(websocket_flow)()