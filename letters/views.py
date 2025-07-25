from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Letter, LetterRecipient
from .serializers import LetterSerializer, LetterCreateSerializer
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
import boto3
import uuid
import requests

#클로바 STT 호출 함수
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
        result = response.json()
        return result.get("text", "")
    else:
        print("STT 실패!")
        return ""

# 오디오 텍스트 변환 API - 프론트에서 audio_url을 전달 받아 처리
class ClovaSpeechToTextView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print("request.data:", request.data)
        audio_url = request.data.get('audio_url')
        print("audio_url:", audio_url)

        if not audio_url:
            return Response(
                {"error": "audio_url이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # S3에서 음성파일을 다운로드
            response_file = requests.get(audio_url)
            response_file.raise_for_status()
            audio_data = response_file.content

            # 클로바 STT API 호출
            api_url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=Kor"
            headers = {
                "X-NCP-APIGW-API-KEY-ID": settings.NCP_CLIENT_ID,
                "X-NCP-APIGW-API-KEY": settings.NCP_CLIENT_SECRET,
                "Content-Type": "application/octet-stream",
            }
            response = requests.post(api_url, headers=headers, data=audio_data)

            if response.status_code == 200:
                result = response.json()
                transcript = result.get("text", "")
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
        data = request.data
        user = request.user

        receiver_list = data.get("receiver_list", [])
        audio_url = data.get("audio_url")
        transcript = data.get("transcript", "")  # 프론트에서 받은 transcript 사용

        if not receiver_list or not audio_url:
            return Response({"error": "receiver_list와 audio_url은 필수입니다."}, status=400)

        try:
            # 1. Letter 생성 (transcript는 프론트에서 받은 값 사용)
            letter = Letter.objects.create(
                sender=user,
                paper_color=data.get("paper_color", "white"),
                scheduled_at=data.get("scheduled_at"),
                transcript=transcript,
                audio_url=audio_url,
            )

            # 2. 각 수신자에 대해 LetterRecipient 생성
            for receiver in receiver_list:
                email = receiver.get("email")
                if not email:
                    continue

                recipient = LetterRecipient.objects.create(
                    letter=letter,
                    email=email,
                )

                try:
                    letter_url = f"https://your-frontend-url.com/letters/{letter.id}"
                    send_mail(
                        subject="DearVoice에서 새로운 음성 편지가 도착했습니다",
                        message=f"DearVoice에서 새로운 음성 편지를 받았습니다.\n아래 링크를 클릭하여 편지를 확인하세요:\n{letter_url}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"이메일 전송 실패: {e}")

            return Response(LetterSerializer(letter).data, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

        # S3 업로드 API
class S3UploadView(APIView):
    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "파일이 없습니다."}, status=400)

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        filename = f"uploads/{uuid.uuid4()}.webm"
        s3.upload_fileobj(file_obj, settings.AWS_STORAGE_BUCKET_NAME, filename)

        url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{filename}"

        return Response({"url": url})

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