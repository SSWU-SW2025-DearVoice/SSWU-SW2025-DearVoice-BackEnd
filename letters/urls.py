from django.urls import path
from .views import LetterCreateView, LetterListView, LetterDetailView, MyPageLettersView


urlpatterns = [
    path('create/', LetterCreateView.as_view(), name='letter-create'),
    path('list/', LetterListView.as_view(), name='letter-list'),
    path('<int:pk>/', LetterDetailView.as_view(), name='letter-detail'),
     path("mypage/", MyPageLettersView.as_view()),
]
