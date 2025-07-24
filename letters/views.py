# views.py
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Letter
from .serializers import LetterSerializer
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

def clova_speech_to_text(file_url):
    response_file = requests.get(file_url)
    audio_data = response_file.content

    api_url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=Kor"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.NCP_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": settings.NCP_CLIENT_SECRET,
        "Content-Type": "application/octet-stream",
    }

    response = requests.post(api_url, headers=headers, data=audio_data)
    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        print("STT 실패:", response.text)
        return ""

class LetterCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LetterSerializer(data=request.data)
        if serializer.is_valid():
            letter = serializer.save(sender=request.user)

            # STT URL 기반 처리
            stt_result = clova_speech_to_text(letter.audio_file)
            if stt_result:
                letter.transcript = stt_result
                letter.save()

            # 이메일 전송
            if letter.receiver_email:
                try:
                    letter_url = f"https://your-frontend-url.com/letters/{letter.id}"
                    send_mail(
                        subject="DearVoice에서 새로운 음성 편지가 도착했습니다",
                        message=f"DearVoice에서 새로운 음성 편지를 받았습니다.\n아래 링크를 클릭하여 편지를 확인하세요:\n{letter_url}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[letter.receiver_email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print("이메일 전송 실패:", e)

            return Response(LetterSerializer(letter).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LetterListView(ListAPIView):
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Letter.objects.filter(Q(sender=user) | Q(receiver_email=user.email))

class LetterDetailView(RetrieveAPIView):
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [AllowAny]
