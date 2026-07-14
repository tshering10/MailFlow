from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmailScheduleViewSet

router = DefaultRouter()
router.register('emails', EmailScheduleViewSet, basename='emails')

urlpatterns = [
    path('', include(router.urls)),
]