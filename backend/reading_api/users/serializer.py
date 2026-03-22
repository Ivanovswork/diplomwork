from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, ConfirmEmailKey
import uuid

class UserRGSTRSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'password_confirm', 'subscription_type']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        validated_data['is_account_active'] = False  # Неактивен до подтверждения
        validated_data['is_active'] = False
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    new_password_confirm = serializers.CharField()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'is_account_active', 'subscription_type']
        read_only_fields = ['id']
