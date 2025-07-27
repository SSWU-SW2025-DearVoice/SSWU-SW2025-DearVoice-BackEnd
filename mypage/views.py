from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from letters.models import Letter, LetterRecipient
from .serializers import SentLetterSerializer, ReceivedLetterSerializer
from django.db.models import Q
from django.shortcuts import get_object_or_404

# 페이지네이션
class LetterPagination(PageNumberPagination):
    page_size = 5

# 보낸 편지함
class SentLettersView(ListAPIView):
    serializer_class = SentLetterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LetterPagination

    def get_queryset(self):
        return Letter.objects.filter(sender=self.request.user).order_by('-created_at')

# 받은 편지함
class ReceivedLettersView(ListAPIView):
    serializer_class = ReceivedLetterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LetterPagination

    def get_queryset(self):
        user = self.request.user
        received_ids = LetterRecipient.objects.filter(
            Q(user=user) | Q(email=user.email)
        ).values_list("letter_id", flat=True)
        return Letter.objects.filter(id__in=received_ids).order_by('-created_at')
    
class MarkLetterAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, letter_id):
        user = request.user

        # 수신자 정보 조회
        recipient = get_object_or_404(
            LetterRecipient,
            letter_id=letter_id,
            email=user.email
        )

        if recipient.is_read:
            return Response({"message": "이미 읽음 처리된 편지입니다."}, status=200)

        recipient.is_read = True
        recipient.save()

        return Response({"message": "편지가 읽음으로 표시되었습니다."}, status=200)