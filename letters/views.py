from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.conf import settings
import boto3
import uuid
from .utils import send_letter_email,clova_stt_from_file
from .models import Letter, LetterRecipient
from .serializers import (
    LetterSerializer,
    LetterCreateSerializer,
    LetterTranscriptUpdateSerializer,
)



# STT 변환 API
class ClovaSpeechToTextView(APIView):
    permission_classes = [IsAuthenticated]

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
        serializer = LetterCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            letter = serializer.save()

            # 이메일 발송
            for r in letter.recipients.all():
                send_letter_email(r.email, letter.id)

            return Response(LetterSerializer(letter).data, status=201)
        else:
            return Response(serializer.errors, status=400)


# S3 업로드용 API
class S3UploadView(APIView):
    permission_classes = [IsAuthenticated]

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
        return Letter.objects.filter(
            Q(sender=user) | Q(recipients__user=user) | Q(recipients__email=user.email)
        ).distinct().prefetch_related('recipients').order_by('-created_at')


# 편지 상세 조회 API
class LetterDetailView(RetrieveAPIView):
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [AllowAny]


class LetterTranscriptUpdateView(generics.UpdateAPIView):
    queryset = Letter.objects.all()
    serializer_class = LetterTranscriptUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 현재 사용자(sender)가 작성한 편지만 수정 가능
        return self.queryset.filter(sender=self.request.user)
