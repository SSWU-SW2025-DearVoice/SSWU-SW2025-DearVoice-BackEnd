from rest_framework import serializers
from .models import SkyVoiceLetter

class SkyVoiceLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkyVoiceLetter
        fields = '__all__'
        read_only_fields = ['user', 'reply_text', 'reply_voice_file', 'created_at', 'replied_at']
