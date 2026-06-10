from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db import transaction
from .models import User, ConfirmEmailKey, PasswordResetKey
from .serializers import (
    UserRGSTRSerializer, UserLoginSerializer,
    UserChangePasswordSerializer, UserSerializer,
    PasswordResetRequestSerializer, PasswordResetVerifySerializer,
    PasswordResetConfirmSerializer
)
from .utils import generate_key, send_password_reset_email


class RegistrUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRGSTRSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                token, _ = Token.objects.get_or_create(user=user)

            return Response({
                "status": "Регистрация успешна.",
                "user_id": user.id,
                "token": token.key,
                "user": UserSerializer(user).data
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
            request,
            username=serializer.validated_data['email'],
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


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Шаг 1: пользователь вводит email, получает код на почту"""
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()

        # Не раскрываем существование email: одинаковый успешный ответ в любом случае.
        if user:
            # Удаляем старые ключи сброса для этого пользователя
            PasswordResetKey.objects.filter(user=user).delete()

            key_obj = PasswordResetKey.objects.create(
                user=user,
                key=generate_key()
            )
            try:
                send_password_reset_email(email, key_obj.key)
            except Exception:
                return Response({
                    "error": "Не удалось отправить письмо. Проверьте настройки почты на сервере."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        return Response({
            "status": "Если email зарегистрирован, код для сброса отправлен"
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_verify(request):
    """Шаг 2: пользователь вводит код, проверяем его"""
    serializer = PasswordResetVerifySerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)
            reset_key = PasswordResetKey.objects.get(user=user, key=code, is_used=False)
            # Отмечаем ключ как использованный, чтобы код был одноразовым
            reset_key.is_used = True
            reset_key.save()

            return Response({
                "status": "Код подтвержден. Можете установить новый пароль.",
                "verified": True
            }, status=status.HTTP_200_OK)
        except (User.DoesNotExist, PasswordResetKey.DoesNotExist):
            return Response({
                "error": "Неверный код сброса пароля"
            }, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Шаг 3: пользователь вводит новый пароль"""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)
            # Проверяем, что ключ существует и использован (прошел верификацию)
            reset_key = PasswordResetKey.objects.get(user=user, key=code, is_used=True)

            user.set_password(serializer.validated_data['new_password'])
            user.save()

            # Удаляем ключ после успешной смены
            reset_key.delete()

            return Response({
                "status": "Пароль успешно изменен. Можете войти."
            }, status=status.HTTP_200_OK)
        except (User.DoesNotExist, PasswordResetKey.DoesNotExist):
            return Response({
                "error": "Ошибка сброса пароля. Попробуйте начать заново."
            }, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
