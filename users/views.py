from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import SignupSerializer

class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({'message': '회원가입 성공'}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignupView(APIView):

    @swagger_auto_schema(
        operation_summary="회원가입 API",
        operation_description="user_id, email, password, nickname을 입력받아 회원가입을 처리합니다.",
        request_body=SignupSerializer,
        responses={
            201: openapi.Response(description="회원가입 성공"),
            400: openapi.Response(description="입력 값 오류"),
        }
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': '회원가입 성공'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)