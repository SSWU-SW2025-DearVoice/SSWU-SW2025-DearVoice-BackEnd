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
            'reply_voice_file',
            'paper_color',
            'scheduled_at',
            'is_sent',
            'created_at',
            'replied_at',
        ]
        read_only_fields = [
            'user',
            'reply_text',
            'reply_voice_file',
            'created_at',
            'replied_at',
        ]

    def validate_scheduled_at(self, value):
        if value and timezone.is_naive(value):
            seoul = pytz.timezone('Asia/Seoul')
            value = seoul.localize(value)
        return value.astimezone(pytz.UTC)