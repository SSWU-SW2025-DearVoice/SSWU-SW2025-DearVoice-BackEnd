from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Letter

@shared_task
def send_scheduled_letters():
    now = timezone.now()
    letters = Letter.objects.filter(is_sent=False, scheduled_at__lte=now)
    for letter in letters:
        if letter.receiver_email:
            send_mail(
                subject='DearVoice에서 도착한 편지 알림',
                message=f"{letter.sender.email} 님이 보내신 편지가 도착했습니다.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[letter.receiver_email],
                fail_silently=False,
            )
        letter.is_sent = True
        letter.save()
        print(f"[예약발송] Letter from {letter.sender.email} 예약발송 및 이메일 알림 완료!")