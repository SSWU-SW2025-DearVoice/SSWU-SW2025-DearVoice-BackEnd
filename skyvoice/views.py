from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import PermissionDenied
import logging
from .models import SkyVoiceLetter
from .serializers import SkyVoiceLetterSerializer
from .services import make_ai_reply
from .tasks import generate_ai_reply_async
from letters.utils import clova_stt_from_file

logger = logging.getLogger(__name__)

# SkyVoice 편지 생성 (STT + AI 답장 포함)
class SkyVoiceLetterCreateView(generics.CreateAPIView):
    serializer_class = SkyVoiceLetterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        letter = serializer.save(user=self.request.user)
        audio_url = letter.audio_url

        transcript = ""
        if audio_url:
            transcript = clova_stt_from_file(audio_url)
            if transcript:
                letter.content_text = transcript
            else:
                logger.warning(f"[STT 실패] letter.id={letter.id}, audio_url={audio_url}")
                letter.content_text = "[음성 텍스트 변환 실패]"
            letter.save()

        if transcript:
            generate_ai_reply_async.delay(letter.id)

# S3 URL 기반 STT 테스트용 API
@method_decorator(csrf_exempt, name='dispatch')
class SkyVoiceTranscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        audio_url = request.data.get('audio_url')
        if not audio_url:
            return Response({"error": "audio_url이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transcript = clova_stt_from_file(audio_url)
            return Response({
                "transcript": transcript,
                "success": True
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[STT 변환 오류] audio_url={audio_url}, error={str(e)}")
            return Response({
                "error": f"텍스트 변환 실패: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 편지 상세 조회 (본인만 조회 가능)
class SkyVoiceLetterDetailView(generics.RetrieveAPIView):
    queryset = SkyVoiceLetter.objects.all()
    serializer_class = SkyVoiceLetterSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("본인의 편지만 조회할 수 있습니다.")
        return obj

# 내가 보낸 편지 목록 조회
class SkyVoiceLetterListView(generics.ListAPIView):
    serializer_class = SkyVoiceLetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SkyVoiceLetter.objects.filter(user=self.request.user).order_by('-created_at')