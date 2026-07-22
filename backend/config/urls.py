from http import HTTPStatus
import os

from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
import redis


def health_check(request):
    try:
        connection.ensure_connection()
        db_status = 'ok'
    except Exception:
        db_status = 'error'

    try:
        redis_client = redis.from_url(
            os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        redis_client.ping()
        redis_status = 'ok'
    except Exception:
        redis_status = 'error'

    overall = 'ok' if db_status == 'ok' and redis_status == 'ok' else 'degraded'

    return JsonResponse(
        {
            'status': overall,
            'database': db_status,
            'redis': redis_status,
        },
        status=HTTPStatus.OK if overall == 'ok' else HTTPStatus.SERVICE_UNAVAILABLE,
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name="health_check"),
    path('api/users/', include('apps.users.urls')),
    path('api/', include('apps.emails.urls')),
    path('accounts/', include('allauth.urls')),
]
