from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import SkyVoiceLetter
from .services import make_ai_reply
import logging
import traceback

logger = logging.getLogger(__name__)

@shared_task
def send_scheduled_voiceletters():
    now = timezone.now()
    letters = SkyVoiceLetter.objects.filter(is_sent=False, scheduled_at__lte=now)

    for letter in letters:
        try:
            subject = f"{letter.receiver_name}에서 도착한 편지 알림"
            message = "DearVoice에 접속해 소중한 메시지를 확인해보세요 💌"

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[letter.user.email],
                fail_silently=False,
            )

            letter.is_sent = True
            letter.save()
            print(f"[SkyVoice] {letter.id}번 편지 발송 완료!")

        except Exception as e:
            print(f"[SkyVoice 오류] {letter.id} 발송 실패: {e}")

@shared_task
def generate_ai_reply_async(letter_id):
    try:
        letter = SkyVoiceLetter.objects.get(pk=letter_id)
        make_ai_reply(letter)
        logger.info(f"[AI] Letter {letter_id} 답장 생성 완료")
    except SkyVoiceLetter.DoesNotExist:
        logger.warning(f"[AI] Letter {letter_id} 존재하지 않음")
    except Exception as e:
        logger.error(f"[AI] Letter {letter_id} 답장 생성 실패: {e}")
        logger.debug(traceback.format_exc())