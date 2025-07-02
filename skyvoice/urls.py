from django.urls import path
from .views import SkyVoiceLetterCreateView

urlpatterns = [
    path('create/', SkyVoiceLetterCreateView.as_view(), name='skyvoice-create'),
]
