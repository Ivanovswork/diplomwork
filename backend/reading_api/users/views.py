from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import User, ConfirmEmailKey
from .serializers import (
    UserRGSTRSerializer, UserLoginSerializer,
    UserChangePasswordSerializer, UserSerializer
)
from .utils import generate_key, send_confirmation_email


class RegistrUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRGSTRSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            key_obj = ConfirmEmailKey.objects.create(
                user=user,
                key=generate_key()
            )
            send_confirmation_email(user.email, key_obj.key)

            return Response({
                "status": "Регистрация успешна. Проверьте email.",
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_email(request, key):
    try:
        confirm_key = ConfirmEmailKey.objects.get(key=key)
        user = confirm_key.user
        user.is_account_active = True
        user.is_active = True
        user.save()
        confirm_key.delete()
        return Response({
            "status": "Email подтвержден. Можете войти."
        }, status=status.HTTP_200_OK)
    except ConfirmEmailKey.DoesNotExist:
        return Response({
            "status": "Ключ не найден"
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        if user:
            if not user.is_account_active:
                return Response({"error": "Подтвердите email"}, status=403)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": UserSerializer(user).data
            })
        return Response({"error": "Неверный email/пароль"}, status=401)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    request.user.auth_token.delete()
    return Response({"status": "Выход выполнен"})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = UserChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({"error": "Неверный старый пароль"}, status=400)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({"status": "Пароль изменен"})
    return Response(serializer.errors, status=400)
