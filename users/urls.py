from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import SignupView, CheckUserIdView, CheckEmailView, me_view, GoogleLoginAPIView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),  
    path('login/google/', GoogleLoginAPIView.as_view(), name='google_login'),
    path('check/user-id/', CheckUserIdView.as_view(), name='check_user_id'),
    path('check/email/', CheckEmailView.as_view(), name='check_email'),
    path('me/', me_view, name='me_view'),
]