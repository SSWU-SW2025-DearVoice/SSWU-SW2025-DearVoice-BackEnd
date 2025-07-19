import requests
from django.conf import settings

def transcribe_audio(audio_file):
    url = "https://clovaspeech-gw.ncloud.com/external/v1/recognizer/file"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.CLOVA_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": settings.CLOVA_CLIENT_SECRET,
    }

    params = {
        "language": "ko-KR",
        "completion": "sync"
    }

    # `audio_file`은 Django FileField 객체 → `open()` 필요
    with audio_file.open('rb') as f:
        files = {
            'media': f
        }
        response = requests.post(url, headers=headers, params=params, files=files)
        response.raise_for_status()
        result = response.json()

    return result.get('text', '')
