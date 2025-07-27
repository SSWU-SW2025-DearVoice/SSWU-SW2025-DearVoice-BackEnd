from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from letters.models import Letter, LetterRecipient
from .serializers import SentLetterSerializer, ReceivedLetterSerializer
from django.db.models import Q

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