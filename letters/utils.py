import os
import requests
import logging
from dotenv import load_dotenv
from django.core.mail import send_mail
from django.conf import settings
import ffmpeg
import tempfile
import requests
from letters.models import Letter

load_dotenv()
logger = logging.getLogger(__name__)

def convert_webm_to_wav(file_url):
    input_file = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
    output_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

    print(f"[DEBUG] 입력 파일 경로: {input_file.name}")
    print(f"[DEBUG] 출력 파일 경로: {output_file.name}")

    # S3에서 webm 파일 다운로드
    res = requests.get(file_url)
    input_file.write(res.content)
    input_file.close()

    # ffmpeg로 변환 (덮어쓰기 허용)
    try:
        ffmpeg.input(input_file.name).output(output_file.name, ac=1, ar=16000).overwrite_output().run()
    except Exception as e:
        print(f"[FFMPEG ERROR]: {e}")
        raise

    return output_file.name

CLOVA_API_URL = "https://clovaspeech-gw.ncloud.com/recognizer/upload?language=ko-KR"
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "")

HEADERS = {
    "X-CLOVASPEECH-API-KEY": CLOVA_API_KEY
}

def clova_stt_from_file(file_url):
    try:
        wav_path = convert_webm_to_wav(file_url)

        print(f"[DEBUG] 변환된 wav 파일 경로: {wav_path}")
        print(f"[DEBUG] 파일 크기: {os.path.getsize(wav_path)} bytes")

        
        with open(wav_path, 'rb') as wav_file:
            audio_data = wav_file.read()

        # ✅ 동기 API 엔드포인트
        CLOVA_API_URL = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=Kor"

        headers = {
            "X-NCP-APIGW-API-KEY-ID": settings.NCP_CLIENT_ID,
            "X-NCP-APIGW-API-KEY": settings.NCP_CLIENT_SECRET,
            "Content-Type": "application/octet-stream",
        }
        
        response = requests.post(CLOVA_API_URL, headers=headers, data=audio_data)
        print("[DEBUG] Clova 응답 상태코드:", response.status_code)
        print("[DEBUG] Clova 응답 본문:", response.text)
        response.raise_for_status()
        return response.json().get("text")
    
    except Exception as e:
        logger.error(f"[STT 변환 실패]: {e}")
        return None


def send_letter_email(email, letter_id):
    try:
        letter = Letter.objects.get(id=letter_id)
        letter_url = f"{settings.FRONTEND_BASE_URL}/mypage/received/{letter.uuid}"
        send_mail(
            subject="DearVoice에서 새로운 보이스레터가 도착했습니다",
            message=f"DearVoice에서 새로운 보이스레터를 받았습니다.\n아래 링크를 클릭하여 편지를 확인하세요:\n{letter_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"[이메일] 전송 실패: {e}")