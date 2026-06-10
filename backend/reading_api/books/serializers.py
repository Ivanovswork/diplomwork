from rest_framework import serializers
from django.core.exceptions import ValidationError
from users.models import User
from users.serializers import UserSerializer
from .models import UserConnection, Book
import fitz  # PyMuPDF
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import io


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


def extract_epub_content(content_bytes):
    """Извлекает текст из EPUB и группирует по 10 абзацев на страницу"""
    try:
        # io.BytesIO нужен потому что epub.read_epub ожидает file-like объект
        book = epub.read_epub(io.BytesIO(content_bytes))
        all_paragraphs = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                html_content = item.get_content().decode('utf-8')
                soup = BeautifulSoup(html_content, 'html.parser')

                # Извлекаем абзацы
                paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text:
                        all_paragraphs.append(text)
        
        print(f"✅ EPUB extracted {len(all_paragraphs)} paragraphs")
        
        # Группируем по 10 абзацев на страницу
        pages = []
        for i in range(0, len(all_paragraphs), 10):
            page_paragraphs = all_paragraphs[i:i+10]
            pages.append('\n\n'.join(page_paragraphs))
        
        print(f"📄 Created {len(pages)} pages (10 paragraphs per page)")
        
        # Возвращаем список страниц
        return pages
    except Exception as e:
        print(f"EPUB extraction error: {e}")
        import traceback
        traceback.print_exc()
        return []


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
        if not (filename.endswith('.pdf') or filename.endswith('.epub')):
            raise ValidationError("Только PDF или EPUB файлы")

        file.seek(0)
        content = file.read()

        if filename.endswith('.pdf'):
            header = content[:4]
            if header != b'%PDF':
                raise ValidationError("Некорректный PDF файл")
        elif filename.endswith('.epub'):
            # Проверка валидности EPUB
            try:
                epub.read_epub(io.BytesIO(content))
            except Exception as e:
                print(f"EPUB validation warning: {e}")
                # Мягкая валидация - разрешаем загрузку даже если есть предупреждения
                pass

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
        content = file.read()
        validated_data['content'] = content

        filename = file.name.lower()

        if filename.endswith('.epub'):
            # Для EPUB извлекаем текст (возвращает список страниц по 10 абзацев)
            pages = extract_epub_content(content)
            validated_data['pages_count'] = len(pages)
            validated_data['format'] = 'epub'
            # Сохраняем текст с разделителем страниц
            if hasattr(self.Meta.model, 'extracted_text'):
                validated_data['extracted_text'] = '\n|||||PAGE_BREAK|||||\n'.join(pages)
                print(f"💾 Saved {len(pages)} pages, total text length: {len(validated_data['extracted_text'])}")
        else:
            # PDF
            validated_data['format'] = 'pdf'
            try:
                import time
                start = time.time()
                print(f"⏳ Starting fitz.open for PDF...")
                doc = fitz.open(stream=content, filetype="pdf")
                validated_data['pages_count'] = len(doc)
                elapsed = time.time() - start
                print(f"✅ PDF processed: {validated_data['pages_count']} pages in {elapsed:.2f}s")
                doc.close()
            except Exception as e:
                print(f"⚠️ PDF processing error: {e}")
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
        if not (filename.endswith('.pdf') or filename.endswith('.epub')):
            raise ValidationError("Только PDF или EPUB файлы")

        file.seek(0)
        content = file.read()

        if filename.endswith('.pdf'):
            header = content[:4]
            if header != b'%PDF':
                raise ValidationError("Некорректный PDF файл")
        elif filename.endswith('.epub'):
            try:
                epub.read_epub(io.BytesIO(content))
            except Exception as e:
                print(f"EPUB validation warning: {e}")
                # Мягкая валидация - разрешаем загрузку
                pass

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
        
        filename = file.name.lower()
        
        if filename.endswith('.epub'):
            extracted_text = extract_epub_content(content)
            paragraphs = [p for p in extracted_text.split('\n\n') if p.strip()]
            pages_count = max(1, len(paragraphs))
            book_format = 'epub'
        else:
            try:
                import time
                start = time.time()
                print(f"⏳ Starting fitz.open for child's PDF...")
                doc = fitz.open(stream=content, filetype="pdf")
                pages_count = len(doc)
                elapsed = time.time() - start
                print(f"✅ Child's PDF processed: {pages_count} pages in {elapsed:.2f}s")
                doc.close()
            except Exception as e:
                print(f"⚠️ Child's PDF processing error: {e}")
                pages_count = 0
            book_format = 'pdf'

        book = Book.objects.create(
            user=child,
            name=validated_data['name'],
            content=content,
            pages_count=pages_count,
            status='in_progress',
            daily_goal=validated_data.get('daily_goal', 5),
            uploaded_by=self.context['request'].user,
            format=book_format
        )
        return book


class BookListSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    uploaded_by_id = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    format = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'name', 'pages_count', 'status', 'daily_goal',
            'upload_date', 'is_owner', 'can_delete', 'uploaded_by_name',
            'uploaded_by_id', 'is_active', 'format'
        ]

    def get_format(self, obj):
        # Безопасное получение формата книги
        return getattr(obj, 'format', 'pdf') or 'pdf'

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

    def get_is_active(self, obj):
        return obj.status == 'in_progress'