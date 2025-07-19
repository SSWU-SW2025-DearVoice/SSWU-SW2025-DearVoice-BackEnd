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