from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Letter, LetterRecipient
from .serializers import LetterSerializer, LetterCreateSerializer
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
    """음성 파일을 텍스트로 변환하는 공통 함수"""
    file_obj.seek(0)
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
        result = response.json()
        return result.get("text", "")
    else:
        print("STT 실패!")
        return ""

# 텍스트 변환 전용 API
class TranscribeAudioView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return Response(
                {"error": "audio_file이 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 음성을 텍스트로 변환
            transcript = clova_speech_to_text(audio_file)
            
            if transcript:
                return Response({
                    "transcript": transcript,
                    "success": True,
                    "message": "음성이 성공적으로 텍스트로 변환되었습니다."
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "transcript": "",
                    "success": False,
                    "message": "음성을 텍스트로 변환할 수 없습니다."
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"텍스트 변환 오류: {e}")
            return Response({
                "error": "텍스트 변환 중 오류가 발생했습니다.",
                "success": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 편지 생성 API (텍스트 변환 포함)
class LetterCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LetterCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            letter = serializer.save()
            # 음성 파일을 텍스트로 변환
            try:
                stt_result = clova_speech_to_text(letter.audio_file)
                if stt_result:
                    letter.transcript = stt_result
                    letter.save()
            except Exception as e:
                print(f"==> STT 오류: {e}")

            # 다중 수신자: LetterRecipient별로 메일 발송
            for recipient in letter.recipients.all():
                target_email = recipient.email
                if recipient.user and recipient.user.email:
                    target_email = recipient.user.email
                if target_email:
                    try:
                        letter_url = f"https://your-frontend-url.com/letters/{letter.id}"
                        send_mail(
                            subject="DearVoice에서 새로운 음성 편지가 도착했습니다",
                            message=f"DearVoice에서 새로운 음성 편지를 받았습니다.\n아래 링크를 클릭하여 편지를 확인하세요:\n{letter_url}",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[target_email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print(f"이메일 전송 실패: {e}")

            # 응답
            return Response({"letter_id": letter.id}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LetterListView(ListAPIView):
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        sent_qs = Letter.objects.filter(sender=user)
        received_letter_ids = LetterRecipient.objects.filter(
            Q(user=user) | Q(email=user.email)
        ).values_list('letter_id', flat=True)
        received_qs = Letter.objects.filter(id__in=received_letter_ids)
        return sent_qs.union(received_qs)

class LetterDetailView(RetrieveAPIView):
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [AllowAny]  # 비회원도 접근 가능