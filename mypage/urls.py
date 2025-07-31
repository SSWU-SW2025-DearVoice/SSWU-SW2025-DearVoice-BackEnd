from django.urls import path
from .views import (
    SentLettersView,
    ReceivedLettersView,
    MarkLetterAsReadView
)

urlpatterns = [
    path('sent/', SentLettersView.as_view(), name='sent-letters'),
    path('received/', ReceivedLettersView.as_view(), name='received-letters'),
    path('letter/<uuid:letter_id>/read/', MarkLetterAsReadView.as_view(), name='letter-mark-read'),
]