
from rest_framework import serializers
from letters.models import Letter

class MyPageLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = ['id', 'receiver_email', 'transcript', 'paper_color', 'created_at']
