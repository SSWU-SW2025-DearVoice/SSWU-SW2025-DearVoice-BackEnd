from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

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


class LoginSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(user_id=data['user_id'], password=data['password'])
        if not user:
            raise serializers.ValidationError("아이디 또는 비밀번호가 올바르지 않습니다.")
        if not user.is_active:
            raise serializers.ValidationError("비활성화된 계정입니다.")

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'user_id': user.user_id,
                'email': user.email,
                'nickname': user.nickname
            }
        }

