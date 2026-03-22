from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        if not password:
            raise ValueError("Users must have a password")

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_account_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    # ТОЛЬКО твои атрибуты из описания БД
    name = models.CharField(
        max_length=150,
        verbose_name="Имя",
        blank=False
    )
    email = models.EmailField(
        verbose_name="Email",
        unique=True,
        blank=False
    )
    is_account_active = models.BooleanField(
        verbose_name="Аккаунт активен",
        default=False,
        help_text="Меняется с 0 на 1 при подтверждении email"
    )
    is_superuser = models.BooleanField(
        verbose_name="Является суперюзером",
        default=False,
        help_text="Принадлежность к администраторам"
    )
    subscription_type = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Активна (10 книг)'),
            ('inactive', 'Не активна (1 книга)'),
        ],
        default='inactive',
        verbose_name="Тип подписки",
        help_text="Лимит загружаемых книг: 10 при активной, 1 при неактивной"
    )

    # Стандартные поля Django
    is_staff = models.BooleanField(
        verbose_name="Статус персонала",
        default=False,
        help_text="Определяет, может ли пользователь войти в админку"
    )
    is_active = models.BooleanField(
        verbose_name="Аккаунт активен",
        default=True,
        help_text="Деактивирует аккаунт вместо удаления"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.name} ({self.email})"


# Добавь в конец файла models.py в users:
class ConfirmEmailKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Key for {self.user.email}"
