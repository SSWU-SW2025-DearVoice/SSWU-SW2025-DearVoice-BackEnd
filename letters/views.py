from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.conf import settings
import boto3
import uuid
from .utils import send_letter_email

from .models import Letter, LetterRecipient
from .serializers import LetterSerializer, LetterCreateSerializer
from .utils import clova_stt_from_file 

# STT 변환 API
class ClovaSpeechToTextView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        audio_url = request.data.get('audio_url')
        if not audio_url:
            return Response({"error": "audio_url이 필요합니다."}, status=400)

        transcript = clova_stt_from_file(audio_url)
        if transcript:
            return Response({
                "transcript": transcript,
                "success": True,
                "message": "음성이 성공적으로 텍스트로 변환되었습니다."
            }, status=200)
        else:
            return Response({
                "transcript": "",
                "success": False,
                "message": "음성을 텍스트로 변환할 수 없습니다."
            }, status=400)

# 편지 생성 API
class LetterCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        user = request.user

        receiver_list = data.get("receiver_list", [])
        audio_url = data.get("audio_url")
        transcript = data.get("transcript", "")

        if not receiver_list or not audio_url:
            return Response({"error": "receiver_list와 audio_url은 필수입니다."}, status=400)

        try:
            # Letter 생성
            letter = Letter.objects.create(
                sender=user,
                paper_color=data.get("paper_color", "white"),
                scheduled_at=data.get("scheduled_at"),
                transcript=transcript,
                audio_url=audio_url,
            )

            # 수신자 처리
            for receiver in receiver_list:
                email = receiver.get("email")
                if not email:
                    continue

                recipient = LetterRecipient.objects.create(letter=letter, email=email)

                # 이메일 발송
                send_letter_email(email, letter.id)

            return Response(LetterSerializer(letter).data, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

# S3 업로드용 API
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
        ext = file_obj.name.split('.')[-1]
        filename = f"uploads/{uuid.uuid4()}.{ext}"
        s3.upload_fileobj(file_obj, settings.AWS_STORAGE_BUCKET_NAME, filename)

        url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{filename}"
        return Response({"url": url})

# 편지 목록 조회 API
class LetterListView(ListAPIView):
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        sent = Letter.objects.filter(sender=user)
        received_ids = LetterRecipient.objects.filter(
            Q(user=user) | Q(email=user.email)
        ).values_list('letter_id', flat=True)
        received = Letter.objects.filter(id__in=received_ids)
        
        return sent.union(received).prefetch_related('recipients').order_by('-created_at')

# 편지 상세 조회 API
class LetterDetailView(RetrieveAPIView):
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [AllowAny]