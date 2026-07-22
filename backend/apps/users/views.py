from rest_framework import generics
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import UserRegisterSerializer, UserSerializer
from .serializers import ActivityLogSerializer
from .models import ActivityLog

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {
                    "error": "Refresh Token is required"
                },
                status = status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            if str(token['user_id']) != str(request.user.id):
                return Response(
                    {
                        "error": "Token does not belong to the authenticated user"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            token.blacklist()
            return Response({
                "message": "Successfully logged out"
            },
            status = status.HTTP_200_OK
            )
        except TokenError:
            return Response({
                "error": "Invalid Token"
            }, status = status.HTTP_400_BAD_REQUEST
            )

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:3000/' # Default frontend URL, can be configured later
    client_class = OAuth2Client

class ActivityView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ActivityLog.objects.filter(user=self.request.user)
