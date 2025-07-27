from django.urls import path
from .views import (
    SkyVoiceLetterCreateView,
    SkyVoiceTranscribeView,
    SkyVoiceLetterDetailView,
    SkyVoiceLetterListView,
)

from django.urls import path
from .views import (
    SkyVoiceLetterCreateView,
    SkyVoiceTranscribeView,
    SkyVoiceLetterDetailView,
    SkyVoiceLetterListView,
)

urlpatterns = [
    # 편지 생성
    path('letters/', SkyVoiceLetterCreateView.as_view(), name='skyvoice-letter-create'),

    # 편지 목록 조회 (내가 쓴 편지들)
    path('letters/list/', SkyVoiceLetterListView.as_view(), name='skyvoice-letter-list'),

    # 편지 상세 조회
    path('letters/<int:pk>/', SkyVoiceLetterDetailView.as_view(), name='skyvoice-letter-detail'),

    # STT 변환 (프론트에서 텍스트 미리 확인용)
    path('letters/transcribe/', SkyVoiceTranscribeView.as_view(), name='skyvoice-letter-transcribe'),
]