from rest_framework import serializers
from .models import SkyVoiceLetter
from django.utils import timezone
import pytz

class SkyVoiceLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkyVoiceLetter
        fields = [
            'id',
            'user',
            'receiver_name',
            'audio_url',
            'content_text',
            'reply_text',
            'reply_voice_url',
            'color',
            'scheduled_at',
            'is_sent',
            'created_at',
            'replied_at',
            'receiver_age',
            'receiver_gender',
            'receiver_type',
            'title',
        ]
        read_only_fields = [
            'user',
            'reply_text',
            'reply_voice_url',
            'created_at',
            'replied_at',
        ]

    def validate_scheduled_at(self, value):
        if value and timezone.is_naive(value):
            seoul = pytz.timezone('Asia/Seoul')
            value = seoul.localize(value)
        return value.astimezone(pytz.UTC)

    def create(self, validated_data):
        letter = SkyVoiceLetter.objects.create(**validated_data)

        scheduled_at = validated_data.get("scheduled_at")
        now_utc = timezone.now()

        # 즉시 발송 조건 추가
        if scheduled_at is None or scheduled_at <= now_utc:
            letter.is_sent = True
            letter.scheduled_at = now_utc if scheduled_at is None else scheduled_at
            letter.save()

        return letter

