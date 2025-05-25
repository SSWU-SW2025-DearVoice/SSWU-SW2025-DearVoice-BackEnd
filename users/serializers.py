from rest_framework import serializers
from .models import CustomUser

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
