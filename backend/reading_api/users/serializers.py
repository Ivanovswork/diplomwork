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
        password = data.get('password')
        password_confirm = data.get('password_confirm')
        email = data.get('email')

        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": ["Пароли не совпадают"]})
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": ["Пользователь с таким email уже существует"]})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # Упрощенный production-режим: аккаунт сразу активен (без email-подтверждения)
        validated_data['is_account_active'] = True
        validated_data['is_active'] = True
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


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data
