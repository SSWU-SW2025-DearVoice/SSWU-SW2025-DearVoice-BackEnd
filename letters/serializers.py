from rest_framework import serializers
from .models import Letter, LetterRecipient
from users.models import CustomUser
import json
import pytz
from django.utils import timezone

class LetterSerializer(serializers.ModelSerializer):
    recipients = serializers.SerializerMethodField()

    class Meta:
        model = Letter
        fields = ['id', 'sender', 'audio_file', 'transcript', 'paper_color',
                  'created_at', 'scheduled_at', 'is_sent', 'recipients']

        read_only_fields = ['sender']

    def get_recipients(self, obj):
        return [
            {"user_id": r.user.id if r.user else None, "email": r.email}
            for r in obj.recipients.all()
        ]

    def validate_scheduled_at(self, value):
        if value and timezone.is_naive(value):
            seoul = pytz.timezone('Asia/Seoul')
            value = seoul.localize(value)
        return value.astimezone(pytz.UTC)

class LetterCreateSerializer(serializers.ModelSerializer):
    recipients = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = Letter
        fields = ['audio_file', 'paper_color', 'recipients']

    def to_internal_value(self, data):
        print("DEBUG recipients:", data.get('recipients'))
        recipients = data.get('recipients')
        if isinstance(recipients, str):
            try:
                data['recipients'] = json.loads(recipients)
            except Exception:
                raise serializers.ValidationError({'recipients': '잘못된 형식의 JSON입니다.'})
        return super().to_internal_value(data)

    def create(self, validated_data):
        recipients_data = validated_data.pop('recipients')
        letter = Letter.objects.create(**validated_data)
        for recipient in recipients_data:
            user = None
            email = recipient.get('email')
            user_id = recipient.get('user_id')
            if user_id:
                try:
                    user = CustomUser.objects.get(pk=user_id)
                except CustomUser.DoesNotExist:
                    pass
            LetterRecipient.objects.create(letter=letter, user=user, email=email)
        return letter