from django.urls import path
from .views import (
    SentLettersView,
    ReceivedLettersView,
    MarkLetterAsReadView,
    DeleteAccountView,
    DeleteSentLetterView,
)

urlpatterns = [
    path('sent/', SentLettersView.as_view(), name='sent-letters'),
    path('received/', ReceivedLettersView.as_view(), name='received-letters'),
    path('letter/<uuid:letter_id>/read/', MarkLetterAsReadView.as_view(), name='letter-mark-read'),
    path("delete-account/", DeleteAccountView.as_view(), name="delete-account"),
    path("sent/delete/<str:letter_type>/<uuid:letter_id>/", DeleteSentLetterView.as_view(), name="delete-sent-letter"),
]