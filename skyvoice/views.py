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
                audio_file.seek(0)
                transcript = clova_speech_to_text(audio_file)
            else:
                # S3에서 파일을 다운로드해서 처리
                import requests
                response = requests.get(audio_url)
                response.raise_for_status()
                transcript = clova_speech_to_text(response.content)

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