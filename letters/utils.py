import os
import requests
import logging
from dotenv import load_dotenv
from django.core.mail import send_mail
from django.conf import settings

load_dotenv()
logger = logging.getLogger(__name__)

CLOVA_API_URL = "https://clovaspeech-gw.ncloud.com/recognizer/upload"
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "")

HEADERS = {
    "X-CLOVASPEECH-API-KEY": CLOVA_API_KEY
}

def clova_stt_from_file(file_url, filename="audio.webm", mime="audio/webm"):
    try:
        file_response = requests.get(file_url)
        file_response.raise_for_status()
    except Exception as e:
        logger.error(f"[STT] 파일 다운로드 실패: {e}")
        return None

    files = {
        "media": (filename, file_response.content, mime)
    }

    data = {
        "language": "ko-KR"
    }

    try:
        response = requests.post(CLOVA_API_URL, headers=HEADERS, data=data, files=files)
        response.raise_for_status()
        return response.json().get("text")
    except Exception as e:
        logger.error(f"[STT] 클로바 요청 실패: {e}")
        logger.error(f"[STT] 응답 내용: {getattr(response, 'text', '없음')}")
        return None

def send_letter_email(email, letter_id):
    try:
        letter_url = f"{settings.FRONTEND_BASE_URL}/letters/{letter_id}"
        send_mail(
            subject="DearVoice에서 새로운 보이스레터가 도착했습니다",
            message=f"DearVoice에서 새로운 보이스레터를 받았습니다.\n아래 링크를 클릭하여 편지를 확인하세요:\n{letter_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"[이메일] 전송 실패: {e}")