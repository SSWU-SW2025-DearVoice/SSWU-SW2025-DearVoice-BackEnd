from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from dj_rest_auth.registration.serializers import RegisterSerializer

# 일반 회원가입용 (SignupView에서 사용)
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
            nickname=validated_data.get('nickname', ''),
            is_new_user=True,            # 신규 사용자
            is_social_login=False        # 일반 회원가입
        )
        return user