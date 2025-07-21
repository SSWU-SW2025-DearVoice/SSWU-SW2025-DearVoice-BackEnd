from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignupSerializer
from django.conf import settings
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView

User = get_user_model()

class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({'message': '회원가입 성공'}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GoogleLoginAPIView(APIView):
    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'detail': 'id_token이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            idinfo = google_id_token.verify_oauth2_token(
                id_token, requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
        except Exception as e:
            return Response({'detail': '구글 토큰 검증 실패', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        email = idinfo.get('email')
        google_uid = idinfo.get('sub')
        nickname = idinfo.get('name', '')
        if not email or not google_uid:
            return Response({'detail': '구글 프로필 정보 부족'}, status=status.HTTP_400_BAD_REQUEST)
        if not nickname:
            nickname = email.split('@')[0]
        
        user = User.objects.filter(email=email).first()
        if user is None:
            user_id = f'google_{google_uid}'
            user = User.objects.create_user(
                user_id=user_id,
                email=email,
                nickname=nickname
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'user_id': user.user_id,
                'email': user.email,
                'nickname': user.nickname,
            }
        }, status=status.HTTP_200_OK)
    
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter