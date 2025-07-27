from rest_framework import serializers
from letters.models import Letter, LetterRecipient
from users.models import CustomUser

class RecipientInfoSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='user.nickname', default=None)
    display_id = serializers.SerializerMethodField()

    class Meta:
        model = LetterRecipient
        fields = ['email', 'nickname', 'display_id', 'is_read']

    def get_display_id(self, obj):
        user = getattr(obj, 'user', None)
        if user:
            return user.user_id or user.email
        return obj.email

class SentLetterSerializer(serializers.ModelSerializer):
    recipients = RecipientInfoSerializer(many=True)

    class Meta:
        model = Letter
        fields = ['id', 'transcript', 'paper_color', 'created_at', 'recipients']

class SenderInfoSerializer(serializers.ModelSerializer):
    display_id = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['user_id', 'nickname', 'email', 'display_id']

    def get_display_id(self, obj):
        return obj.user_id or obj.email

class ReceivedLetterSerializer(serializers.ModelSerializer):
    sender = SenderInfoSerializer()

    class Meta:
        model = Letter
        fields = ['id', 'transcript', 'paper_color', 'created_at', 'sender']