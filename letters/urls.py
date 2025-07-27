from django.urls import path
from .views import (
    LetterCreateView,
    LetterListView,
    LetterDetailView,
    S3UploadView,
    ClovaSpeechToTextView,
)

urlpatterns = [
    # S3 업로드
    path('upload/', S3UploadView.as_view(), name='letter-upload'),

    # STT 처리
    path('transcribe/', ClovaSpeechToTextView.as_view(), name='letter-transcribe'),

    # 편지 생성
    path('', LetterCreateView.as_view(), name='letter-create'),

    # 편지 목록
    path('list/', LetterListView.as_view(), name='letter-list'),

    # 편지 상세
    path('<uuid:pk>/', LetterDetailView.as_view(), name='letter-detail'),
]