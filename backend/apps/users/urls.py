from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserProfileView, GoogleLogin, ActivityView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='user_register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('activity/', ActivityView.as_view(), name="activity_log"),

    path('google/', GoogleLogin.as_view(), name='google_login'),
]
