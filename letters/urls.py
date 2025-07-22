from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.LetterCreateView.as_view(), name='letter-create'),
    path('transcribe/', views.TranscribeAudioView.as_view(), name='transcribe-audio'),  # 텍스트 변환(추가)
    path('list/', views.LetterListView.as_view(), name='letter-list'),
    path('<uuid:pk>/', views.LetterDetailView.as_view(), name='letter-detail'),
]