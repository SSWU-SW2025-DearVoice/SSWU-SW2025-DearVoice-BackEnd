from rest_framework import serializers
from letters.models import Letter, LetterRecipient
from users.models import CustomUser

class RecipientInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterRecipient
        fields = ['email', 'is_read']

class SentLetterSerializer(serializers.ModelSerializer):
    recipients = RecipientInfoSerializer(many=True)

    class Meta:
        model = Letter
        fields = ['id', 'transcript', 'paper_color', 'created_at', 'recipients']

class SenderInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['user_id', 'nickname', 'email']

class ReceivedLetterSerializer(serializers.ModelSerializer):
    sender = SenderInfoSerializer()

    class Meta:
        model = Letter
        fields = ['id', 'transcript', 'paper_color', 'created_at', 'sender']