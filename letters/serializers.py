from rest_framework import serializers
from .models import Letter
from django.utils import timezone
import pytz

class LetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = '__all__'
        read_only_fields = ['sender', 'sent_at']

    def validate_scheduled_at(self, value):
        if value and timezone.is_naive(value):
            seoul = pytz.timezone('Asia/Seoul')
            value = seoul.localize(value)
        return value.astimezone(pytz.UTC)