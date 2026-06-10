from django.core.mail import send_mail
from django.conf import settings
import secrets
import string

def generate_key():
    """Генерирует уникальный ключ подтверждения (64 символа)"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))

def send_confirmation_email(user_email, key):
    """Отправляет письмо подтверждения на email"""
    # URL берётся из переменной окружения или используется дефолтный
    import os
    base_url = os.environ.get('BASE_URL', 'http://80.78.254.95')
    confirm_url = f"{base_url}/api/users/confirm-email/{key}/"
    send_mail(
        'Подтверждение email - Reading API',
        f'Перейдите по ссылке для подтверждения: {confirm_url}',
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )


def send_password_reset_email(user_email, key):
    """Отправляет код для сброса пароля на email"""
    import os
    base_url = os.environ.get('BASE_URL', 'http://80.78.254.95')
    reset_url = f"{base_url}/forgot-password.html"
    send_mail(
        'Сброс пароля - Reading Tracker',
        f'Ваш код для сброса пароля: {key}\n\n'
        f'Перейдите по ссылке: {reset_url}\n\n'
        f'Введите этот код в приложении, чтобы установить новый пароль.\n'
        f'Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.',
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )