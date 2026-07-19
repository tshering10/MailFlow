from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/emails/', consumers.EmailStatusConsumer.as_asgi()),
]