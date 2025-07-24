from django.urls import path
from . import views
#프론트 추가
# from .views import upload_audio_file
from .views import ClovaSpeechToTextView

urlpatterns = [
    path('create/', views.LetterCreateView.as_view(), name='letter-create'),
    path('transcribe/', views.ClovaSpeechToTextView.as_view(), name='transcribe-audio'),  # 수정된 부분
    # path('transcribe/', views.TranscribeAudioView.as_view(), name='transcribe-audio'),  # 텍스트 변환(추가)
    path('list/', views.LetterListView.as_view(), name='letter-list'),
    path('<uuid:pk>/', views.LetterDetailView.as_view(), name='letter-detail'),
    #프론트 추가
    path('upload/', views.S3UploadView.as_view(), name='s3-upload'),
    path("skyvoice/transcribe/", ClovaSpeechToTextView.as_view()),
    # path('letters/upload/', upload_audio_file),
]