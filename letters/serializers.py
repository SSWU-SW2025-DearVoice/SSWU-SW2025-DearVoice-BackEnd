import pytz
from django.utils import timezone
from rest_framework import serializers
from .models import Letter, LetterRecipient
from users.models import CustomUser


class LetterSerializer(serializers.ModelSerializer):
    recipients = serializers.SerializerMethodField()

    class Meta:
        model = Letter
        fields = [
            'id',
            'sender',
            'audio_file',
            'audio_url',
            'transcript',
            'paper_color',
            'created_at',
            'scheduled_at',
            'is_sent',
            'recipients',
        ]
        read_only_fields = ['sender']

    def get_recipients(self, obj):
        return [
            {
                "user_id": getattr(r.user, "id", None),
                "email": r.email,
                "is_read": r.is_read,
            }
            for r in obj.recipients.all()
        ]

    def validate_scheduled_at(self, value):
        if value:
            if timezone.is_naive(value):
                seoul = pytz.timezone('Asia/Seoul')
                value = seoul.localize(value)

            if value < timezone.now():
                raise serializers.ValidationError("예약 발송 시간은 현재 시간 이후여야 합니다.")
            return value.astimezone(pytz.UTC)
        return value


class LetterCreateSerializer(serializers.ModelSerializer):
    recipients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        write_only=True
    )

    class Meta:
        model = Letter
        fields = [
            'audio_file',
            'audio_url',
            'paper_color',
            'scheduled_at',
            'transcript',
            'recipients',
        ]

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

            LetterRecipient.objects.create(
                letter=letter,
                user=user,
                email=email
            )

        return letter