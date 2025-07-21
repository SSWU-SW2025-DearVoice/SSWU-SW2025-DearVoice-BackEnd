# letters/utils.py

import os
import requests

def clova_stt_from_file(file_url):
    CLOVA_API_URL = "https://clovaspeech-gw.ncloud.com/recognizer/upload"
    headers = {
        "X-CLOVASPEECH-API-KEY": os.getenv("CLOVA_API_KEY")  # .env 파일 또는 환경변수에서 API 키 가져오기
    }

    data = {
        "language": "ko-KR",
    }

    # S3 Presigned URL 기반 다운로드
    response = requests.get(file_url)
    if response.status_code != 200:
        return ""

    files = {
        "media": ('audio.mp3', response.content)
    }

    response = requests.post(CLOVA_API_URL, headers=headers, data=data, files=files)

    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        print("CLOVA STT 오류:", response.text)
        return ""
