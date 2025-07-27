from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import LetterRecipient, Letter
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_scheduled_letters():
    now = timezone.now()
    letters = Letter.objects.filter(is_sent=False, scheduled_at__lte=now)

    for letter in letters:
        recipients = letter.recipients.all()
        letter_sent = False

        for recipient in recipients:
            email = recipient.email
            if not email:
                continue

            try:
                letter_url = f"{settings.FRONTEND_BASE_URL}/letters/{letter.id}"
                send_mail(
                    subject="DearVoice에서 편지가 도착했습니다",
                    message=f"{letter.sender.email} 님이 보낸 음성 편지가 도착했습니다.\n확인 링크: {letter_url}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                logger.info(f"[예약발송] {email} 에게 편지 발송 완료!")
                letter_sent = True
            except Exception as e:
                logger.error(f"[예약발송 오류] {email} 전송 실패: {e}")

        if letter_sent:
            letter.is_sent = True
            letter.save()