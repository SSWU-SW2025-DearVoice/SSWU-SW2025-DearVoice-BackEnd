from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from letters.models import Letter, LetterRecipient
from .serializers import SentLetterSerializer, ReceivedLetterSerializer
from django.db.models import Q
from django.shortcuts import get_object_or_404

class MyPageLettersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # 내가 보낸 편지 (누구에게 보냈는지와 읽었는지)
        sent_letters = Letter.objects.filter(sender=user)
        received_letter_ids = LetterRecipient.objects.filter(
            Q(user=user) | Q(email=user.email)
        ).values_list("letter_id", flat=True)
        received_letters = Letter.objects.filter(id__in=received_letter_ids)

        return Response({
            "sent_letters": SentLetterSerializer(sent_letters, many=True).data,
            "received_letters": ReceivedLetterSerializer(received_letters, many=True).data
        })
    
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