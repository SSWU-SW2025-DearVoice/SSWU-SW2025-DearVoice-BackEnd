import pytz
from django.utils import timezone
from rest_framework import serializers
from .models import Letter, LetterRecipient
from users.models import CustomUser
from letters.tasks import send_letter_task



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
        recipients_data = validated_data.pop("recipients")
        scheduled_at = validated_data.get("scheduled_at")
        now = timezone.now()

        # Letter 인스턴스 먼저 생성
        letter = Letter.objects.create(**validated_data)

        # 수신자 저장
        for recipient_data in recipients_data:
            LetterRecipient.objects.create(letter=letter, **recipient_data)

        # 즉시 전송 조건 확인 및 처리
        if scheduled_at is None or scheduled_at <= now:
            letter.is_sent = True
            letter.scheduled_at = now  # scheduled_at이 None이면 지금으로 설정
            letter.save()

            # Celery 태스크 등록 (예: 실제 전송 작업 등)
            send_letter_task.apply_async(args=[str(letter.id)])

        return letter




class LetterTranscriptUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = ['transcript']
