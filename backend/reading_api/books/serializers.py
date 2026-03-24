from rest_framework import serializers
from django.core.exceptions import ValidationError
from users.models import User
from users.serializers import UserSerializer
from .models import UserConnection, Book
import fitz  # PyMuPDF


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
        fields = ['id', 'user1_data', 'user2_data', 'connection_type', 'is_parent_flag', 'is_child_flag', 'status']

    def get_status(self, obj):
        if obj.connection_type == 'parent_child':
            return 'active'
        if obj.connection_type == 'parent_request':
            return 'parent_pending'
        if obj.connection_type == 'child_request':
            return 'child_pending'
        return 'pending'


class BookListSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    uploaded_by_id = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'name', 'pages_count', 'status', 'daily_goal', 'upload_date',
                  'is_owner', 'can_delete', 'uploaded_by_name', 'uploaded_by_id']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request:
            return obj.user == request.user
        return False

    def get_can_delete(self, obj):
        request = self.context.get('request')
        if not request:
            return False

        # Владелец книги может удалить
        if obj.user == request.user:
            return True

        # Родитель может удалить любую книгу ребенка
        from .models import UserConnection
        is_parent = UserConnection.objects.filter(
            user1=request.user,
            user2=obj.user,
            connection_type='parent_child',
            is_parent_flag=True,
            is_child_flag=True
        ).exists()

        if is_parent:
            return True

        return False

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.name
        return None

    def get_uploaded_by_id(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.id
        return None


class BookUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=True)
    daily_goal = serializers.IntegerField(default=5, min_value=1, required=False)

    class Meta:
        model = Book
        fields = ['name', 'file', 'daily_goal']

    def validate_file(self, file):
        if not file:
            raise ValidationError("Файл не выбран")

        filename = file.name.lower()
        if not filename.endswith('.pdf'):
            raise ValidationError("Только PDF файлы")

        file.seek(0)
        header = file.read(4)
        if header != b'%PDF':
            raise ValidationError("Некорректный PDF файл")
        file.seek(0)

        if file.size > 100 * 1024 * 1024:
            raise ValidationError("Файл слишком большой (максимум 100MB)")
        return file

    def validate(self, data):
        user = self.context['request'].user
        book_limit = 10 if user.subscription_type == 'active' else 1
        user_books = Book.objects.filter(
            user=user,
            status__in=['in_progress', 'completed']
        ).count()
        if user_books >= book_limit:
            raise ValidationError(f"Лимит: {book_limit} книг для вашей подписки")
        return data

    def create(self, validated_data):
        file = validated_data.pop('file')
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['uploaded_by'] = user
        validated_data['content'] = file.read()

        try:
            import fitz
            doc = fitz.open(stream=validated_data['content'], filetype="pdf")
            validated_data['pages_count'] = len(doc)
            doc.close()
        except Exception as e:
            validated_data['pages_count'] = 0

        validated_data['status'] = 'in_progress'
        book = Book.objects.create(**validated_data)
        return book


class BookUploadToChildSerializer(serializers.Serializer):
    child_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    file = serializers.FileField(write_only=True, required=True)
    daily_goal = serializers.IntegerField(default=5, min_value=1, required=False)

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
        if not file:
            raise ValidationError("Файл не выбран")

        filename = file.name.lower()
        if not filename.endswith('.pdf'):
            raise ValidationError("Только PDF файлы")

        file.seek(0)
        header = file.read(4)
        if header != b'%PDF':
            raise ValidationError("Некорректный PDF файл")
        file.seek(0)

        if file.size > 100 * 1024 * 1024:
            raise ValidationError("Файл слишком большой (максимум 100MB)")
        return file

    def validate(self, data):
        user = self.context['request'].user
        child = User.objects.get(id=data['child_id'])
        book_limit = 10 if child.subscription_type == 'active' else 1
        child_books = Book.objects.filter(
            user=child,
            status__in=['in_progress', 'completed']
        ).count()
        if child_books >= book_limit:
            raise ValidationError(f"У ребенка лимит: {book_limit} книг")
        return data

    def create(self, validated_data):
        child = User.objects.get(id=validated_data['child_id'])
        file = validated_data.pop('file')
        content = file.read()

        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            pages_count = len(doc)
            doc.close()
        except Exception as e:
            pages_count = 0

        book = Book.objects.create(
            user=child,
            name=validated_data['name'],
            content=content,
            pages_count=pages_count,
            status='in_progress',
            daily_goal=validated_data.get('daily_goal', 5),
            uploaded_by=self.context['request'].user
        )
        return book