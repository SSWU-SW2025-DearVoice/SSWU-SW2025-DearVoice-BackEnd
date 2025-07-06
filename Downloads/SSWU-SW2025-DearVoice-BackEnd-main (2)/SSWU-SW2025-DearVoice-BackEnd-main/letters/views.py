from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Letter
from .serializers import LetterSerializer
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny

class LetterCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LetterSerializer(data=request.data)
        if serializer.is_valid():
            letter = serializer.save(sender=request.user)
            return Response(LetterSerializer(letter).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LetterListView(ListAPIView):
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Letter.objects.filter(Q(sender=user) | Q(receiver_email=user.email))

class LetterDetailView(RetrieveAPIView):
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [AllowAny]  # 비회원도 접근 가능