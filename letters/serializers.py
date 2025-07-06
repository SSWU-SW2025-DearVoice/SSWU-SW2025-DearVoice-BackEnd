# letters/serializers.py

from rest_framework import serializers
from .models import Letter

class LetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = '__all__'
        read_only_fields = ['sender', 'sent_at']
