from django.urls import path
from .views import SkyVoiceLetterCreateView, SkyVoiceLetterAIReplyView, SkyVoiceTranscribeView, SkyVoiceLetterDetailView, SkyVoiceLetterListView

urlpatterns = [
    path('create/', SkyVoiceLetterCreateView.as_view(), name='skyvoice-create'),
    path('reply/ai/<int:pk>/', SkyVoiceLetterAIReplyView.as_view(), name='skyvoice-ai-reply'),
    path('transcribe/', SkyVoiceTranscribeView.as_view()),
    path('<int:pk>/', SkyVoiceLetterDetailView.as_view(), name='skyvoice-detail'),
    #프론트 추가
    path('list/', SkyVoiceLetterListView.as_view())
]