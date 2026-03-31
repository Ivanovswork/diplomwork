from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import UserConnection, Book
from .serializers import (
    ConnectionRequestSerializer, ConnectionSerializer,
    BookUploadSerializer, BookUploadToChildSerializer, BookListSerializer
)

User = get_user_model()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_my_id(user):
    return user.id


# ==================== ОБЩИЕ СВЯЗИ ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_connections(request):
    """Все связи текущего пользователя"""
    connections = UserConnection.objects.filter(
        models.Q(user1=request.user) | models.Q(user2=request.user)
    ).select_related('user1', 'user2').order_by('-id')
    serializer = ConnectionSerializer(connections, many=True)
    return Response({
        "my_connections": serializer.data,
        "total": len(serializer.data),
        "active": len([c for c in serializer.data if c['status'] == 'active'])
    })


# ==================== ДРУЗЬЯ ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_friends(request):
    """Список активных друзей"""
    connections = UserConnection.objects.filter(
        models.Q(user1=request.user) | models.Q(user2=request.user),
        connection_type='friendship',
        is_parent_flag=True,
        is_child_flag=True
    ).select_related('user1', 'user2')

    result = []
    for conn in connections:
        friend = conn.user2 if conn.user1 == request.user else conn.user1
        result.append({
            'id': friend.id,
            'name': friend.name,
            'email': friend.email,
            'connection_id': conn.id
        })

    return Response({'friends': result})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_friend_requests(request):
    """Запросы в друзья для текущего пользователя"""
    requests_list = UserConnection.objects.filter(
        user2=request.user,
        connection_type='friendship',
        is_parent_flag=False,
        is_child_flag=False
    ).select_related('user1')
    serializer = ConnectionSerializer(requests_list, many=True)
    return Response({
        "friend_requests": serializer.data,
        "pending_count": len(serializer.data)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_friendship(request):
    """Отправить запрос в друзья"""
    serializer = ConnectionRequestSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        target_user = User.objects.get(id=serializer.validated_data['target_user_id'])

        existing = UserConnection.objects.filter(
            models.Q(user1=request.user, user2=target_user) |
            models.Q(user1=target_user, user2=request.user)
        )
        if existing.exists():
            return Response({"error": "Связь уже существует"}, status=status.HTTP_400_BAD_REQUEST)

        connection = UserConnection.objects.create(
            user1=request.user,
            user2=target_user,
            connection_type='friendship',
            is_parent_flag=False,
            is_child_flag=False
        )
        return Response({
            "message": "Запрос в друзья отправлен",
            "connection": ConnectionSerializer(connection).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_friendship(request):
    """Подтверждение дружбы"""
    target_user_id = request.data.get('target_user_id')
    if not target_user_id:
        return Response({"error": "Нужен target_user_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        connection = UserConnection.objects.get(
            user2=request.user,
            user1_id=target_user_id,
            connection_type='friendship'
        )
        connection.is_parent_flag = True
        connection.is_child_flag = True
        connection.save()
        return Response({
            "message": "Теперь вы друзья!",
            "connection": ConnectionSerializer(connection).data
        })
    except UserConnection.DoesNotExist:
        return Response({"error": "Запрос не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_friendship(request):
    """Отклонение запроса в друзья"""
    target_user_id = request.data.get('target_user_id')
    if not target_user_id:
        return Response({"error": "Нужен target_user_id"}, status=status.HTTP_400_BAD_REQUEST)

    connections = UserConnection.objects.filter(
        user2=request.user,
        user1_id=target_user_id,
        connection_type='friendship'
    )
    if connections.exists():
        connections.delete()
        return Response({"message": "Запрос отклонен"})
    return Response({"error": "Запрос не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_friend(request):
    """Удаление из друзей"""
    target_user_id = request.data.get('target_user_id')
    if not target_user_id:
        return Response({"error": "Нужен target_user_id"}, status=status.HTTP_400_BAD_REQUEST)

    connections = UserConnection.objects.filter(
        models.Q(
            (models.Q(user1=request.user, user2_id=target_user_id) |
             models.Q(user1_id=target_user_id, user2=request.user))
        ) &
        models.Q(connection_type='friendship')
    )
    if connections.exists():
        connections.delete()
        return Response({"message": "Друг удален"})
    return Response({"error": "Дружба не найдена"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_friend_by_email(request):
    """Добавить друга по email"""
    email = request.data.get('email')

    if not email:
        return Response({'error': 'Email не указан'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        target_user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    if target_user == request.user:
        return Response({'error': 'Нельзя добавить самого себя'}, status=status.HTTP_400_BAD_REQUEST)

    existing = UserConnection.objects.filter(
        models.Q(user1=request.user, user2=target_user) |
        models.Q(user1=target_user, user2=request.user)
    )

    if existing.exists():
        conn = existing.first()
        if conn.connection_type == 'friendship' and conn.is_parent_flag and conn.is_child_flag:
            return Response({'error': 'Уже друзья'}, status=status.HTTP_400_BAD_REQUEST)
        elif conn.connection_type == 'friendship':
            return Response({'error': 'Запрос уже отправлен'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Связь уже существует'}, status=status.HTTP_400_BAD_REQUEST)

    connection = UserConnection.objects.create(
        user1=request.user,
        user2=target_user,
        connection_type='friendship',
        is_parent_flag=False,
        is_child_flag=False
    )

    return Response({
        'status': 'Запрос отправлен',
        'connection': ConnectionSerializer(connection).data
    }, status=status.HTTP_201_CREATED)


# ==================== РОДИТЕЛЬСКИЙ КОНТРОЛЬ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_parent_connection(request):
    """Родитель отправляет запрос ребенку"""
    serializer = ConnectionRequestSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        target_user = User.objects.get(id=serializer.validated_data['target_user_id'])

        existing = UserConnection.objects.filter(
            models.Q(user1=request.user, user2=target_user) |
            models.Q(user1=target_user, user2=request.user)
        )
        if existing.exists():
            return Response({"error": "Связь уже существует"}, status=status.HTTP_400_BAD_REQUEST)

        connection = UserConnection.objects.create(
            user1=request.user,
            user2=target_user,
            connection_type='parent_request',
            is_parent_flag=True,
            is_child_flag=False
        )
        return Response({
            "message": "Запрос отправлен ребенку",
            "connection": ConnectionSerializer(connection).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_parent_requests(request):
    """Запросы от родителей для текущего пользователя"""
    requests_list = UserConnection.objects.filter(
        user2=request.user,
        connection_type='parent_request',
        is_parent_flag=True,
        is_child_flag=False
    ).select_related('user1')
    serializer = ConnectionSerializer(requests_list, many=True)
    return Response({
        "parent_requests": serializer.data,
        "pending_count": len(serializer.data)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_connection(request):
    """Ребенок подтверждает связь с родителем"""
    target_parent_id = request.data.get('target_parent_id')
    if not target_parent_id:
        return Response({"error": "Нужен target_parent_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        connection = UserConnection.objects.get(
            user1_id=target_parent_id,
            user2=request.user,
            connection_type='parent_request'
        )
        connection.connection_type = 'parent_child'
        connection.is_child_flag = True
        connection.save()
        return Response({
            "message": "Связь активирована!",
            "connection": ConnectionSerializer(connection).data
        })
    except UserConnection.DoesNotExist:
        return Response({"error": "Запрос не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_connection(request):
    """Ребенок отклоняет запрос родителя"""
    target_parent_id = request.data.get('target_parent_id')
    if not target_parent_id:
        return Response({"error": "Нужен target_parent_id"}, status=status.HTTP_400_BAD_REQUEST)

    connection = UserConnection.objects.filter(
        user1_id=target_parent_id,
        user2=request.user,
        connection_type='parent_request'
    )
    if connection.exists():
        connection.delete()
        return Response({"message": "Запрос отклонен"})
    return Response({"error": "Запрос не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_children(request):
    """Список детей для родителя"""
    connections = UserConnection.objects.filter(
        user1=request.user,
        connection_type='parent_child',
        is_parent_flag=True,
        is_child_flag=True
    ).select_related('user2')

    result = []
    for conn in connections:
        result.append({
            'id': conn.user2.id,
            'name': conn.user2.name,
            'email': conn.user2.email,
            'connection_id': conn.id
        })
    return Response({'children': result})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_parents(request):
    """Список родителей для ребенка"""
    connections = UserConnection.objects.filter(
        user2=request.user,
        connection_type='parent_child',
        is_parent_flag=True,
        is_child_flag=True
    ).select_related('user1')

    result = []
    for conn in connections:
        result.append({
            'id': conn.user1.id,
            'name': conn.user1.name,
            'email': conn.user1.email,
            'connection_id': conn.id
        })
    return Response({'parents': result})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_parent_by_email(request):
    """Отправить запрос на родительский контроль по email"""
    email = request.data.get('email')

    if not email:
        return Response({'error': 'Email не указан'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        target_user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    if target_user == request.user:
        return Response({'error': 'Нельзя добавить самого себя'}, status=status.HTTP_400_BAD_REQUEST)

    existing = UserConnection.objects.filter(
        models.Q(user1=request.user, user2=target_user) |
        models.Q(user1=target_user, user2=request.user)
    )

    if existing.exists():
        conn = existing.first()

        if conn.connection_type == 'parent_child' and conn.is_parent_flag and conn.is_child_flag:
            return Response({'error': 'Уже связаны как родитель-ребенок'}, status=status.HTTP_400_BAD_REQUEST)

        if conn.connection_type in ['parent_request', 'child_request']:
            return Response({'error': 'Запрос уже отправлен'}, status=status.HTTP_400_BAD_REQUEST)

        if conn.connection_type == 'friendship' and conn.is_parent_flag and conn.is_child_flag:
            parent_connection = UserConnection.objects.create(
                user1=request.user,
                user2=target_user,
                connection_type='parent_request',
                is_parent_flag=True,
                is_child_flag=False
            )
            return Response({
                'status': 'Запрос на родительский контроль отправлен (дружба сохранена)',
                'connection': ConnectionSerializer(parent_connection).data
            }, status=status.HTTP_201_CREATED)

    connection = UserConnection.objects.create(
        user1=request.user,
        user2=target_user,
        connection_type='parent_request',
        is_parent_flag=True,
        is_child_flag=False
    )

    return Response({
        'status': 'Запрос отправлен',
        'connection': ConnectionSerializer(connection).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_by_child(request):
    """Ребенок инициирует отвязку"""
    target_parent_id = request.data.get('target_parent_id')

    if not target_parent_id:
        return Response({"error": "Нужен target_parent_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        connection = UserConnection.objects.get(
            user1_id=target_parent_id,
            user2=request.user,
            connection_type='parent_child',
            is_parent_flag=True,
            is_child_flag=True
        )

        connection.connection_type = 'child_request'
        connection.is_child_flag = False
        connection.save()

        return Response({
            "message": "Запрос на отвязку отправлен родителю",
            "connection": ConnectionSerializer(connection).data
        })

    except UserConnection.DoesNotExist:
        return Response({"error": "Активная связь не найдена"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_by_parent(request):
    """Родитель полностью удаляет связь"""
    target_child_id = request.data.get('target_child_id')

    if not target_child_id:
        return Response({"error": "Нужен target_child_id"}, status=status.HTTP_400_BAD_REQUEST)

    connections = UserConnection.objects.filter(
        user1=request.user,
        user2_id=target_child_id,
        connection_type__in=['parent_child', 'child_request']
    )
    if connections.exists():
        connections.delete()
        return Response({"message": "Связь удалена"})
    return Response({"error": "Связь не найдена"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_unlink_requests(request):
    """Запросы на отвязку от детей для родителя"""
    requests_list = UserConnection.objects.filter(
        user1=request.user,
        connection_type='child_request',
        is_parent_flag=True,
        is_child_flag=False
    ).select_related('user2')

    result = []
    for conn in requests_list:
        result.append({
            'id': conn.id,
            'child_id': conn.user2.id,
            'child_name': conn.user2.name,
            'child_email': conn.user2.email
        })
    return Response({'unlink_requests': result})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_unlink(request):
    """Родитель подтверждает отвязку ребенка"""
    connection_id = request.data.get('connection_id')

    if not connection_id:
        return Response({"error": "Нужен connection_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        connection = UserConnection.objects.get(
            id=connection_id,
            user1=request.user,
            connection_type='child_request',
            is_parent_flag=True,
            is_child_flag=False
        )
        connection.delete()
        return Response({"message": "Связь удалена"})
    except UserConnection.DoesNotExist:
        return Response({"error": "Запрос не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_unlink(request):
    """Родитель отклоняет запрос на отвязку ребенка"""
    connection_id = request.data.get('connection_id')

    if not connection_id:
        return Response({"error": "Нужен connection_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        connection = UserConnection.objects.get(
            id=connection_id,
            user1=request.user,
            connection_type='child_request',
            is_parent_flag=True,
            is_child_flag=False
        )
        connection.connection_type = 'parent_child'
        connection.is_child_flag = True
        connection.save()
        return Response({"message": "Связь восстановлена"})
    except UserConnection.DoesNotExist:
        return Response({"error": "Запрос не найден"}, status=status.HTTP_404_NOT_FOUND)


# ==================== ЗАПРОСЫ И УВЕДОМЛЕНИЯ ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_requests_count(request):
    """Количество активных запросов"""
    friend_requests_count = UserConnection.objects.filter(
        user2=request.user,
        connection_type='friendship',
        is_parent_flag=False,
        is_child_flag=False
    ).count()

    parent_requests_count = UserConnection.objects.filter(
        user2=request.user,
        connection_type='parent_request',
        is_parent_flag=True,
        is_child_flag=False
    ).count()

    unlink_requests_count = UserConnection.objects.filter(
        user1=request.user,
        connection_type='child_request',
        is_parent_flag=True,
        is_child_flag=False
    ).count()

    total = friend_requests_count + parent_requests_count + unlink_requests_count

    return Response({
        'total': total,
        'friend_requests': friend_requests_count,
        'parent_requests': parent_requests_count,
        'unlink_requests': unlink_requests_count
    })


# ==================== КНИГИ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_book(request):
    """Загрузка книги себе"""
    print("=== UPLOAD BOOK CALLED ===")
    print("Request data:", request.data)
    print("Request FILES:", request.FILES)

    serializer = BookUploadSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        book = serializer.save()
        print(f"Book saved: {book.id} - {book.name}")
        return Response({
            "message": "Книга загружена!",
            "book": BookListSerializer(book, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)
    else:
        print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_book_to_child(request):
    """Загрузка книги ребенку"""
    print("=== UPLOAD BOOK TO CHILD CALLED ===")
    print("Request data:", request.data)
    print("Request FILES:", request.FILES)

    serializer = BookUploadToChildSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        book = serializer.save()
        print(f"Book saved to child: {book.id} - {book.name}")
        return Response({
            "message": "Книга загружена ребенку!",
            "book": BookListSerializer(book, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)
    else:
        print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_books(request):
    """Список своих книг"""
    books = Book.objects.filter(
        user=request.user,
        status__in=['in_progress', 'completed']
    ).order_by('-upload_date')
    serializer = BookListSerializer(books, many=True, context={'request': request})
    return Response({
        "my_books": serializer.data,
        "count": len(serializer.data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_child_books(request, child_id):
    """Список книг ребенка"""
    if not UserConnection.objects.filter(
            user1=request.user, user2_id=child_id,
            connection_type='parent_child',
            is_parent_flag=True, is_child_flag=True
    ).exists():
        return Response({"error": "Нет доступа к книгам этого ребенка"}, status=status.HTTP_403_FORBIDDEN)

    books = Book.objects.filter(
        user_id=child_id,
        status__in=['in_progress', 'completed']
    ).order_by('-upload_date')
    serializer = BookListSerializer(books, many=True, context={'request': request})
    return Response({
        "child_books": serializer.data,
        "count": len(serializer.data)
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_book(request, book_id):
    """Удалить книгу"""
    try:
        book = Book.objects.get(id=book_id)

        # Проверка прав: владелец книги может удалить
        is_owner = book.user == request.user

        # Проверка: родитель может удалить книгу ребенка
        is_parent = UserConnection.objects.filter(
            user1=request.user,
            user2=book.user,
            connection_type='parent_child',
            is_parent_flag=True,
            is_child_flag=True
        ).exists()

        if not is_owner and not is_parent:
            return Response({"error": "Нет прав для удаления"}, status=status.HTTP_403_FORBIDDEN)

        # Если книга уже завершена, просто удаляем контент
        if book.status == 'completed':
            book.content = None
            book.save(update_fields=['content'])
            return Response({"message": "Контент книги удален"})

        book.content = None
        book.status = 'deleted'
        book.save(update_fields=['content', 'status'])

        return Response({"message": "Книга удалена"})
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_book_daily_goal(request, book_id):
    """Обновить дневную цель книги"""
    try:
        book = Book.objects.get(id=book_id)

        # Проверка прав: либо владелец книги, либо родитель владельца
        is_owner = book.user == request.user
        is_parent = UserConnection.objects.filter(
            user1=request.user,
            user2=book.user,
            connection_type='parent_child',
            is_parent_flag=True,
            is_child_flag=True
        ).exists()

        if not is_owner and not is_parent:
            return Response({"error": "Нет прав для изменения"}, status=status.HTTP_403_FORBIDDEN)

        daily_goal = request.data.get('daily_goal')

        if daily_goal is None:
            return Response({"error": "daily_goal не указан"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            daily_goal_int = int(daily_goal)
            if daily_goal_int < 1:
                return Response({"error": "Дневная цель должна быть больше 0"}, status=status.HTTP_400_BAD_REQUEST)
            book.daily_goal = daily_goal_int
            book.save(update_fields=['daily_goal'])
        except (TypeError, ValueError):
            return Response({"error": "daily_goal должен быть числом"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Дневная цель обновлена",
            "book": BookListSerializer(book, context={'request': request}).data
        })
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_book_details(request, book_id):
    """Получить детали книги для редактирования"""
    try:
        book = Book.objects.get(id=book_id)

        is_owner = book.user == request.user
        is_parent = UserConnection.objects.filter(
            user1=request.user,
            user2=book.user,
            connection_type='parent_child',
            is_parent_flag=True,
            is_child_flag=True
        ).exists()

        if not is_owner and not is_parent:
            return Response({"error": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "id": book.id,
            "name": book.name,
            "pages_count": book.pages_count,
            "daily_goal": book.daily_goal,
            "status": book.status,
            "upload_date": book.upload_date,
            "is_owner": is_owner
        })
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_book_limit(request):
    """Получить лимит книг для текущего пользователя"""
    user = request.user
    book_limit = 10 if user.subscription_type == 'active' else 1
    current_count = Book.objects.filter(
        user=user,
        status='in_progress'
    ).count()

    return Response({
        'can_upload': current_count < book_limit,
        'current_count': current_count,
        'limit': book_limit,
        'message': f'У вас {current_count} из {book_limit} активных книг'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_child_book_limit(request, child_id):
    """Получить лимит книг для ребенка"""
    try:
        child = User.objects.get(id=child_id)

        # Проверка, что это ребенок текущего пользователя
        is_parent = UserConnection.objects.filter(
            user1=request.user,
            user2=child,
            connection_type='parent_child',
            is_parent_flag=True,
            is_child_flag=True
        ).exists()

        if not is_parent:
            return Response({"error": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

        book_limit = 10 if child.subscription_type == 'active' else 1
        current_count = Book.objects.filter(
            user=child,
            status='in_progress'
        ).count()

        return Response({
            'can_upload': current_count < book_limit,
            'current_count': current_count,
            'limit': book_limit,
            'message': f'У ребенка {current_count} из {book_limit} активных книг'
        })
    except User.DoesNotExist:
        return Response({"error": "Ребенок не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stats(request):
    """Получить статистику пользователя (количество активных книг и страниц)"""
    user = request.user

    # Только активные книги (in_progress)
    books = Book.objects.filter(
        user=user,
        status='in_progress'
    )

    books_count = books.count()

    # Общее количество страниц из всех книг (включая завершенные)
    all_books = Book.objects.filter(user=user)
    total_pages = sum(b.pages_count for b in all_books)

    return Response({
        'books_count': books_count,
        'total_pages': total_pages
    })