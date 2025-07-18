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

def clova_speech_to_text(file_url):
    url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=Kor"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.NCP_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": settings.NCP_CLIENT_SECRET,
        "Content-Type": "application/octet-stream",
    }

    # S3에 업로드된 audio_file을 URL로 다운로드
    response_file = requests.get(file_url)
    if response_file.status_code != 200:
        return ""

    audio_data = response_file.content

    response = requests.post(url, headers=headers, data=audio_data)
    if response.status_code == 200:
        result = response.json()
        return result.get("text", "")
    else:
        return ""

class LetterCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LetterSerializer(data=request.data)
        if serializer.is_valid():
            letter = serializer.save(sender=request.user)

            # Clova Speech API 호출 (S3 URL 기반)
            file_url = letter.audio_file.url
            stt_result = clova_speech_to_text(file_url)
            if stt_result:
                letter.transcript = stt_result
                letter.save()

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

class MyPageLettersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        sent_letters = Letter.objects.filter(sender=user)
        received_letters = Letter.objects.filter(receiver_email=user.email)

        return Response({
            "sent_letters": LetterSerializer(sent_letters, many=True).data,
            "received_letters": LetterSerializer(received_letters, many=True).data
        })
