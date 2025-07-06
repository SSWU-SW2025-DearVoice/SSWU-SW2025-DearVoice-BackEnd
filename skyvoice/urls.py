from django.urls import path
from .views import SkyVoiceLetterCreateView, SkyVoiceLetterReplyView

urlpatterns = [
    path('create/', SkyVoiceLetterCreateView.as_view(), name='skyvoice-create'),
    path('reply/ai/<int:pk>/', SkyVoiceLetterAIReplyView.as_view(), name='skyvoice-ai-reply'),
]
