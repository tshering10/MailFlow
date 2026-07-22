from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ActivityLog

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class ActivityLogSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ActivityLog
        fields = ['id', 'email', 'email_subject', 'action', 'description', 'timestamp']
        read_only_fields = fields

