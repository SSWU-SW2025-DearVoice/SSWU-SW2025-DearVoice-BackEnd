import pytz
from django.utils import timezone
from rest_framework import serializers
from .models import Letter, LetterRecipient
from users.models import CustomUser


class LetterSerializer(serializers.ModelSerializer):
    recipients = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Letter
        fields = [
            'id',
            'sender',
            'audio_url',
            'transcript',
            'paper_color',
            'created_at',
            'scheduled_at',
            'is_sent',
            'recipients',
            'title'
        ]
        read_only_fields = ['sender']

    def get_sender(self, obj):
        user = obj.sender
        return {
            "user_id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "display_id": user.user_id or user.email
        }

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
        child=serializers.DictField(child=serializers.CharField()),
        write_only=True
    )
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Letter
        fields = [
            'sender',
            'audio_url',
            'paper_color',
            'scheduled_at',
            'transcript',
            'recipients',
            'title'
        ]

    def validate(self, attrs):
        # audio_url은 필수
        if not attrs.get('audio_url'):
            raise serializers.ValidationError("audio_url은 필수입니다.")
        return attrs

    def validate_scheduled_at(self, value):
        if value:
            if timezone.is_naive(value):
                seoul = pytz.timezone('Asia/Seoul')
                value = seoul.localize(value)

            if value < timezone.now():
                raise serializers.ValidationError("예약 발송 시간은 현재 시간 이후여야 합니다.")
            return value.astimezone(pytz.UTC)
        return value

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

            LetterRecipient.objects.create(
                letter=letter,
                user=user,
                email=email
            )

        return letter



class LetterTranscriptUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = ['transcript']
