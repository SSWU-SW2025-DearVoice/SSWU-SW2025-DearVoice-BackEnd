from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from letters.models import Letter, LetterRecipient
from django.db.models import Q
from django.shortcuts import get_object_or_404
from skyvoice.models import SkyVoiceLetter

# 페이지네이션
class LetterPagination(PageNumberPagination):
    page_size = 5

# 통합 보낸 편지함
class SentLettersView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LetterPagination

    def get(self, request):
        user = request.user

        letters = Letter.objects.filter(sender=user)
        letter_data = [
            {
                "id": str(l.id),
                "type": "letter",
                "transcript": l.transcript,
                "title": l.title,
                "paper_color": l.paper_color,
                "created_at": l.created_at
            }
            for l in letters
        ]

        skyletters = SkyVoiceLetter.objects.filter(user=user)
        skyletter_data = [
            {
                "id": str(s.id),
                "type": "sky",
                "transcript": s.content_text,
                "title": s.title,
                "paper_color": s.color,
                "created_at": s.created_at
            }
            for s in skyletters
        ]

        combined = letter_data + skyletter_data
        combined.sort(key=lambda x: x["created_at"], reverse=True)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)

# 통합 받은 편지함
class ReceivedLettersView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LetterPagination

    def get(self, request):
        user = request.user

        received_ids = LetterRecipient.objects.filter(
            Q(user=user) | Q(email=user.email)
        ).values_list("letter_id", flat=True)
        letters = Letter.objects.filter(id__in=received_ids)
        letter_data = [
            {
                "id": str(l.id),
                "type": "letter",
                "transcript": l.transcript,
                "title": l.title,
                "paper_color": l.paper_color,
                "created_at": l.created_at,
                "sender_display_id": l.sender.user_id or l.sender.email
            }
            for l in letters
        ]

        skyletters = SkyVoiceLetter.objects.filter(user=user)
        skyletter_data = [
            {
                "id": str(s.id),
                "type": "sky",
                "transcript": s.content_text,
                "title": s.title,
                "reply_text":s.reply_text,
                "paper_color": s.color,
                "created_at": s.created_at,
                "sender_display_id": getattr(s.user, "user_id", None) or getattr(s.user, "email", None)
            }
            for s in skyletters
        ]

        combined = letter_data + skyletter_data
        combined.sort(key=lambda x: x["created_at"], reverse=True)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)

# 읽음 처리
class MarkLetterAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, letter_id):
        user = request.user

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