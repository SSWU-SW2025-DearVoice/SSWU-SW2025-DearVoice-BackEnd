import json
from rest_framework import serializers
from .models import Letter, LetterRecipient
from users.models import CustomUser
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

# ✅ 수정된 부분 시작
class LetterCreateSerializer(serializers.ModelSerializer):
    recipients = serializers.CharField(write_only=True)  # JSON string으로 받음

    class Meta:
        model = Letter
        fields = ['audio_file', 'paper_color', 'scheduled_at', 'transcript', 'recipients', 'audio_url']

    def validate_recipients(self, value):
        try:
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                raise serializers.ValidationError("리스트 형식이어야 합니다.")
            for r in parsed:
                if not isinstance(r, dict) or "email" not in r:
                    raise serializers.ValidationError("각 항목은 email을 포함한 dict이어야 합니다.")
            return parsed
        except json.JSONDecodeError:
            raise serializers.ValidationError("JSON 형식이 아닙니다.")

    def create(self, validated_data):
        recipients_data = validated_data.pop('recipients')
        request = self.context.get("request")
        letter = Letter.objects.create(sender=request.user, **validated_data)
        
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
