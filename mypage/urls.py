from django.urls import path
from .views import MyPageLettersView

urlpatterns = [
    path('letters/', MyPageLettersView.as_view(), name='mypage-letters'),
]