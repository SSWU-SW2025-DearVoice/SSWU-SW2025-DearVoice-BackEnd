from django.shortcuts import render
from rest_framework import generics, permissions
from .models import SkyVoiceLetter
from .serializers import SkyVoiceLetterSerializer

class SkyVoiceLetterCreateView(generics.CreateAPIView):
    serializer_class = SkyVoiceLetterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

