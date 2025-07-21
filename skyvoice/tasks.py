from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from .models import SkyVoiceLetter

@shared_task
def send_scheduled_voiceletters():
    now = timezone.now()
    letters = SkyVoiceLetter.objects.filter(is_sent=False, scheduled_at__lte=now)

    for letter in letters:
        subject = f"{letter.receiver_name}에서 도착한 편지 알림"
        message = "DearVoice에 접속해 소중한 메시지를 확인해보세요 💌"

        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[letter.user.email],
            fail_silently=False,
        )

        letter.is_sent = True
        letter.save()
        print(f"{letter.id}번 편지 발송 완료!")