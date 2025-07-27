from django.urls import path
from .views import MyPageLettersView, MarkLetterAsReadView

urlpatterns = [
    path('letters/', MyPageLettersView.as_view(), name='mypage-letters'),
    path('letter/<uuid:letter_id>/read/', MarkLetterAsReadView.as_view(), name='letter-mark-read'),
]