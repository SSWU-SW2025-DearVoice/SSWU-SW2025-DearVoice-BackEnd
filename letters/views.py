from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Letter
from .serializers import LetterSerializer
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
import requests
from django.conf import settings
from django.core.mail import send_mail
import boto3

def clova_speech_to_text(file_obj):
    audio_data = file_obj.read()
    print("==> 데이터 길이:", len(audio_data))

    api_url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=Kor"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.NCP_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": settings.NCP_CLIENT_SECRET,
        "Content-Type": "application/octet-stream",
    }

    response = requests.post(api_url, headers=headers, data=audio_data)
    print("==> 네이버 응답 status_code:", response.status_code)
    print("==> 네이버 응답 text:", response.text)
    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        print("STT 실패!")
        return ""


class LetterCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LetterSerializer(data=request.data)
        if serializer.is_valid():
            letter = serializer.save(sender=request.user)

            # ✅ presigned URL 필요 없음, 그냥 .url 그대로 사용
            file_url = letter.audio_file.url
            stt_result = clova_speech_to_text(letter.audio_file)
            if stt_result:
                letter.transcript = stt_result
                letter.save()

            # ✅ 이메일 전송 그대로 유지
            receiver_email = letter.receiver_email
            if receiver_email:
                try:
                    letter_url = f"https://your-frontend-url.com/letters/{letter.id}"
                    send_mail(
                        subject="DearVoice에서 새로운 음성 편지가 도착했습니다",
                        message=f"DearVoice에서 새로운 음성 편지를 받았습니다.\n아래 링크를 클릭하여 편지를 확인하세요:\n{letter_url}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[receiver_email],
                        fail_silently=False,
                    )


                except Exception as e:
                    print(f"이메일 전송 실패: {e}")

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
    permission_classes = [AllowAny]  # 비회원도 접근 가능
