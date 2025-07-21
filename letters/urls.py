from django.urls import path
from .views import LetterCreateView, LetterListView, LetterDetailView

urlpatterns = [
    path('create/', LetterCreateView.as_view(), name='letter-create'),
    path('list/', LetterListView.as_view(), name='letter-list'),
    path('<uuid:pk>/', LetterDetailView.as_view(), name='letter-detail'),
]