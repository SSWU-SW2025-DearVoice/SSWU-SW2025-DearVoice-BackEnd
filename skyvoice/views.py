from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import SkyVoiceLetter
from .serializers import SkyVoiceLetterSerializer
from .services import make_ai_reply
from letters.views import clova_speech_to_text
from .utils import generate_presigned_url
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
#프론트 추가
from rest_framework.permissions import IsAuthenticated

class SkyVoiceLetterCreateView(generics.CreateAPIView):
    serializer_class = SkyVoiceLetterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        letter = serializer.save(user=self.request.user)

        if letter.voice_file:
            audio_file_url = generate_presigned_url(letter.voice_file)
            letter.voice_file_url = audio_file_url  # 발급 받은 presigned_url을 DB에 저장 (마이페이지에서 열어볼 수 있게, 근데 임시 접근이기 때문에 제한 시간 있음)
            content_text = clova_speech_to_text(audio_file_url)
            letter.content_text = content_text
            letter.save()
        try:
            make_ai_reply(letter)
        except Exception as e:
            print(f"[SkyVoice] AI 답변 생성 실패: {e}")

class SkyVoiceLetterAIReplyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            letter = SkyVoiceLetter.objects.get(pk=pk)
        except SkyVoiceLetter.DoesNotExist:
            return Response({'detail': 'Letter not found'}, status=status.HTTP_404_NOT_FOUND)

        if letter.reply_text or letter.reply_voice_file:
            return Response({'detail': '이미 답신이 등록된 편지입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            make_ai_reply(letter)
        except Exception as e:
            return Response({'detail': f'AI 답신 생성 오류: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(SkyVoiceLetterSerializer(letter).data, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class SkyVoiceTranscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        audio_file = request.FILES.get('audio_file')
        audio_url = request.data.get('audio_url')

        if not audio_file and not audio_url:
            return Response({"error": "audio_file 또는 audio_url이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if audio_file:
                # 1. 임시 객체에 파일 저장 (필수 필드 기본값, 이 때 파일을 S3에 업로드하려면 모델 객체 파일을 저장해야 되기 때문)
                temp_letter = SkyVoiceLetter.objects.create(
                    user=request.user,
                    voice_file=audio_file,
                    receiver_name="temp",
                    receiver_gender="unknown",
                    receiver_age=0,
                    receiver_type="temp",
                    color="white",
                    title="temp"
                )
                temp_letter.refresh_from_db()
                # 2. presigned URL 발급
                audio_file_url = generate_presigned_url(temp_letter.voice_file)
                # 3. STT 변환
                transcript = clova_speech_to_text(audio_file_url)
                # 4. 임시 객체 삭제
                temp_letter.delete()
            else:
                # S3에서 파일을 다운로드해서 처리
                transcript = clova_speech_to_text(audio_url)

            return Response({
                "transcript": transcript,
                "success": True
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"텍스트 변환 실패: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SkyVoiceLetterDetailView(generics.RetrieveAPIView):
    queryset = SkyVoiceLetter.objects.all()
    serializer_class = SkyVoiceLetterSerializer
    permission_classes = [permissions.IsAuthenticated]

#프론트 추가
class SkyVoiceLetterListView(generics.ListAPIView):
    serializer_class = SkyVoiceLetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SkyVoiceLetter.objects.filter(user=self.request.user).order_by('-created_at')