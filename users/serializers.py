from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from dj_rest_auth.registration.serializers import RegisterSerializer

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['user_id', 'email', 'password', 'nickname']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            user_id=validated_data['user_id'],
            email=validated_data['email'],
            password=validated_data['password'],
            nickname=validated_data.get('nickname', '')
        )
        return user

class CustomRegisterSerializer(RegisterSerializer):
    user_id = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    nickname = serializers.CharField(required=False, allow_blank=True, max_length=20)

    def get_cleaned_data(self):
        return {
            'user_id': self.validated_data.get('user_id', ''),
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
            'nickname': self.validated_data.get('nickname', ''),
        }

    def save(self, request):
        user = super().save(request)
        user.nickname = self.cleaned_data.get('nickname', '')
        user.save()
        return user