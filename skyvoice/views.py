from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import SkyVoiceLetter
from .serializers import SkyVoiceLetterSerializer
import requests

class SkyVoiceLetterCreateView(generics.CreateAPIView):
    serializer_class = SkyVoiceLetterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SkyVoiceLetterAIReplyView(APIView):
    permission_classes = [permissions.IsAuthenticated] 

    def post(self, request, pk):
        try:
            letter = SkyVoiceLetter.objects.get(pk=pk)
        except SkyVoiceLetter.DoesNotExist:
            return Response({'detail': 'Letter not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if letter.reply_text or letter.reply_voice_file:
            return Response({'detail': '이미 답신이 등록된 편지입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        ai_server_url = "http://AI서버주소/ai-reply/" 
        ai_payload = {
            "content_text": letter.content_text,
            "receiver_info": {
                "name": letter.receiver_name,
                "gender": letter.receiver_gender,
                "age": letter.receiver_age,
                "type": letter.receiver_type,
                "special_note": letter.receiver_special_note,
            },
        }
        try:
            ai_response = requests.post(ai_server_url, json=ai_payload, timeout=10)
            ai_response.raise_for_status()
        except requests.RequestException:
            return Response({'detail': 'AI 서버 오류'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        ai_data = ai_response.json()
        letter.reply_text = ai_data.get("reply_text", "")
        letter.reply_voice_file = ai_data.get("reply_voice_url", "")
        letter.replied_at = timezone.now()
        letter.save()

        return Response(SkyVoiceLetterSerializer(letter).data, status=status.HTTP_200_OK)
