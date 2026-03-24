from django.db import models
from django.conf import settings
from users.models import User


class UserConnection(models.Model):
    CONNECTION_TYPES = [
        ('friendship', 'Дружба'),
        ('parent_child', 'Родитель_ребенок'),
        ('child_request', 'Запрос_от_ребенка'),  # Новый тип!
        ('pending', 'Ожидает_подтверждения'),    # Новый тип!
    ]

    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_as_user2')
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPES, verbose_name="Тип")
    is_parent_flag = models.BooleanField(default=False, verbose_name="Флаг родителя")
    is_child_flag = models.BooleanField(default=False, verbose_name="Флаг дочерний")

    class Meta:
        unique_together = ['user1', 'user2', 'connection_type']
        verbose_name = "Связь пользователей"
        verbose_name_plural = "Связи пользователей"

    def __str__(self):
        return f"{self.user1.name} - {self.user2.name} ({self.connection_type})"

    def save(self, *args, **kwargs):
        # Автоматическая логика типов связи
        if self.connection_type == 'parent_child':
            if self.is_parent_flag and self.is_child_flag:
                self.connection_type = 'parent_child'  # Полностью активна
            elif self.is_parent_flag and not self.is_child_flag:
                self.connection_type = 'pending'  # Ожидает ребенка
        super().save(*args, **kwargs)


class Book(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'В процессе'),
        ('completed', 'Закончена'),
        ('deleted', 'Удалена'),
    ]

    name = models.CharField(max_length=255, verbose_name="Наименование")
    pages_count = models.PositiveIntegerField(verbose_name="Количество страниц", default=0)
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', verbose_name="Статус")
    daily_goal = models.PositiveIntegerField(default=5, verbose_name="Дневная цель")
    content = models.BinaryField(verbose_name="Содержимое", null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь",
                             related_name='books')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="Кем загружена", related_name='uploaded_books')

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"

    def __str__(self):
        return f"{self.name} ({self.pages_count} стр.)"
