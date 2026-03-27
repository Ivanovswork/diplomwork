from django.db import models
from datetime import timedelta
from django.core.exceptions import ValidationError
from users.models import User
from books.models import Book, UserConnection
from django.conf import settings


class ReadingSession(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('completed', 'Завершена'),
        ('abandoned', 'Брошена'),
    ]

    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, verbose_name="Книга",
                             related_name='reading_sessions')
    start_page = models.PositiveIntegerField(verbose_name="Начальная страница")
    end_page = models.PositiveIntegerField(verbose_name="Конечная страница", null=True, blank=True)
    start_datetime = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время начала")
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name="Дата и время окончания")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Последняя активность")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Статус")
    pages_read = models.PositiveIntegerField(default=0, verbose_name="Прочитано страниц в сессии")

    class Meta:
        verbose_name = "Сессия чтения"
        verbose_name_plural = "Сессии чтения"

    def __str__(self):
        return f"Сессия {self.book.name} (стр. {self.start_page}-{self.end_page})"


class PageReadingLog(models.Model):
    session = models.ForeignKey(ReadingSession, on_delete=models.CASCADE, verbose_name="Сессия",
                                related_name='page_logs')
    page_number = models.PositiveIntegerField(verbose_name="Номер страницы")
    time_spent = models.DurationField(verbose_name="Время чтения страницы")
    words_count = models.PositiveIntegerField(verbose_name="Количество слов на странице", default=0)
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Время завершения страницы")

    class Meta:
        unique_together = ['session', 'page_number']
        verbose_name = "Лог чтения страницы"
        verbose_name_plural = "Логи чтения страниц"

    def clean(self):
        if self.time_spent < timedelta(seconds=10):
            raise ValidationError("Время чтения должно быть не менее 10 секунд")

    def __str__(self):
        return f"Страница {self.page_number} ({self.time_spent.total_seconds():.0f}с)"


class UserReadingStreak(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_streak')
    current_streak = models.PositiveIntegerField(default=0, verbose_name="Текущий стрик")
    longest_streak = models.PositiveIntegerField(default=0, verbose_name="Самый длинный стрик")
    last_read_date = models.DateField(null=True, blank=True, verbose_name="Дата последнего чтения")

    class Meta:
        verbose_name = "Стрик чтения"
        verbose_name_plural = "Стрики чтения"

    def __str__(self):
        return f"{self.user.name}: {self.current_streak} дней"


class Test(models.Model):
    session = models.ForeignKey(ReadingSession, on_delete=models.CASCADE, verbose_name="Сессия")
    test_status = models.CharField(
        max_length=20,
        choices=[
            ('passed', 'Пройден'),
            ('failed', 'Не пройден'),
        ],
        default='failed',
        verbose_name="Статус теста"
    )
    formation_time = models.DurationField(verbose_name="Время формирования")
    solution_time = models.DurationField(null=True, blank=True, verbose_name="Время решения")

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"

    def __str__(self):
        return f"Тест {self.session} ({self.test_status})"


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Тест")
    text = models.TextField(verbose_name="Текст")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return self.text[:50] + "..."


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Вопрос")
    text = models.CharField(max_length=255, verbose_name="Текст")
    is_correct = models.BooleanField(verbose_name="Правильный ответ")

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f"{self.text[:30]} ({'✓' if self.is_correct else '✗'})"


class Achievement(models.Model):
    name = models.CharField(max_length=100, verbose_name="Наименование")
    is_active = models.BooleanField(default=True, verbose_name="Статус")

    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, verbose_name="Достижение")

    class Meta:
        unique_together = ['user', 'achievement']
        verbose_name = "Достижение пользователя"
        verbose_name_plural = "Достижения пользователей"

    def __str__(self):
        return f"{self.user.name} - {self.achievement.name}"
