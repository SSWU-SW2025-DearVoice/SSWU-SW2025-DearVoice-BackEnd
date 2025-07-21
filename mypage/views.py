from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from letters.models import Letter
from .serializers import MyPageLetterSerializer

class MyPageLettersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        sent_letters = Letter.objects.filter(sender=user)
        received_letters = Letter.objects.filter(receiver_email=user.email)

        return Response({
            "sent_letters": MyPageLetterSerializer(sent_letters, many=True).data,
            "received_letters": MyPageLetterSerializer(received_letters, many=True).data
        })
