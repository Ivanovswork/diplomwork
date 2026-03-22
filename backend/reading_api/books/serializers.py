from rest_framework import serializers
from users.models import User
from users.serializers import UserSerializer
from .models import UserConnection, Book
from django.core.exceptions import ValidationError


class ConnectionRequestSerializer(serializers.Serializer):
    target_user_id = serializers.IntegerField()

    def validate_target_user_id(self, value):
        request = self.context['request']
        if value == request.user.id:
            raise serializers.ValidationError("Нельзя привязать самого себя")
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Пользователь не найден")
        return value


class ConnectionSerializer(serializers.ModelSerializer):
    user1_data = UserSerializer(source='user1', read_only=True)
    user2_data = UserSerializer(source='user2', read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = UserConnection
        fields = ['id', 'user1_data', 'user2_data', 'connection_type',
                  'is_parent_flag', 'is_child_flag', 'status']

    def get_status(self, obj):
        if obj.connection_type == 'parent_child': return 'active'
        if obj.connection_type == 'parent_request': return 'parent_pending'
        if obj.connection_type == 'child_request': return 'child_pending'
        return 'pending'


class BookUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    daily_goal = serializers.IntegerField(default=5, min_value=1, max_value=100)

    class Meta:
        model = Book
        fields = ['name', 'file', 'daily_goal']

    def validate_file(self, file):
        """Проверка PDF файла"""
        # Проверка расширения
        filename = file.name.lower()
        if not filename.endswith('.pdf'):
            raise ValidationError("Только PDF файлы разрешены")

        # Проверка PDF заголовка %PDF-
        file.seek(0)
        header = file.read(4)
        if header != b'%PDF':
            raise ValidationError("Некорректный PDF файл (нет заголовка %PDF)")
        file.seek(0)

        # Лимит размера 100MB
        if file.size > 100 * 1024 * 1024:
            raise ValidationError("Файл слишком большой (максимум 100MB)")

        return file

    def validate(self, data):
        """Лимит книг по подписке"""
        user = self.context['request'].user
        book_limit = 10 if hasattr(user, 'subscription_type') and user.subscription_type == 'active' else 1

        user_books = Book.objects.filter(
            user=user,
            status__in=['in_progress', 'completed']
        ).count()

        if user_books >= book_limit:
            raise ValidationError(f"Лимит: {book_limit} книг(а) для вашей подписки")

        return data

    def create(self, validated_data):
        """Создание книги"""
        file = validated_data.pop('file')
        validated_data['user'] = self.context['request'].user

        # Сохраняем binary content
        validated_data['content'] = file.read()
        validated_data['pages_count'] = 0  # Без PyMuPDF

        # Статус по умолчанию
        validated_data['status'] = 'in_progress'

        book = Book.objects.create(**validated_data)
        return book


class BookUploadToChildSerializer(serializers.Serializer):
    child_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    file = serializers.FileField(write_only=True)
    daily_goal = serializers.IntegerField(default=5, min_value=1, max_value=100)

    def validate_child_id(self, value):
        user = self.context['request'].user
        if not UserConnection.objects.filter(
                user1=user,
                user2_id=value,
                connection_type='parent_child',
                is_parent_flag=True,
                is_child_flag=True
        ).exists():
            raise ValidationError("Это не ваш ребенок")
        return value

    def validate_file(self, file):
        """Тот же код проверки PDF"""
        filename = file.name.lower()
        if not filename.endswith('.pdf'):
            raise ValidationError("Только PDF файлы")

        file.seek(0)
        header = file.read(4)
        if header != b'%PDF':
            raise ValidationError("Некорректный PDF файл")
        file.seek(0)

        if file.size > 100 * 1024 * 1024:
            raise ValidationError("Макс 100MB")
        return file

    def create(self, validated_data):
        child = User.objects.get(id=validated_data['child_id'])
        file = validated_data.pop('file')

        book = Book.objects.create(
            user=child,
            name=validated_data['name'],
            content=file.read(),
            pages_count=0,
            status='in_progress',
            daily_goal=validated_data['daily_goal']
        )
        return book


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'name', 'pages_count', 'status', 'daily_goal', 'upload_date']