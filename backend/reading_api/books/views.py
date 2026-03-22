from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from users.models import User
from .models import UserConnection
from .serializers import ConnectionRequestSerializer, ConnectionSerializer


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_parent_requests(request):
    """Запросы родителей для текущего ребенка"""
    requests = UserConnection.objects.filter(
        user2=request.user,
        connection_type='parent_request'
    ).select_related('user1')

    serializer = ConnectionSerializer(requests, many=True)
    return Response({
        "parent_requests": serializer.data,
        "pending_count": len(serializer.data)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_parent_connection(request):
    """Родитель → запрос ребенку (target_user_id)"""
    serializer = ConnectionRequestSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        target_user = User.objects.get(id=serializer.validated_data['target_user_id'])

        existing = UserConnection.objects.filter(
            models.Q(user1=request.user, user2=target_user) |
            models.Q(user1=target_user, user2=request.user)
        )
        if existing.exists():
            return Response({"error": "Связь уже существует"}, status=400)

        connection = UserConnection.objects.create(
            user1=request.user,
            user2=target_user,
            connection_type='parent_request',
            is_parent_flag=True,
            is_child_flag=False
        )
        return Response({
            "message": "Запрос отправлен",
            "connection": ConnectionSerializer(connection).data
        }, status=201)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_connection(request):
    """Ребенок подтверждает связь с родителем (target_parent_id)"""
    target_parent_id = request.data.get('target_parent_id')
    if not target_parent_id:
        return Response({"error": "Нужен target_parent_id"}, status=400)

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
        return Response({"error": "Запрос не найден"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_connection(request):
    """Ребенок отклоняет связь с родителем (target_parent_id)"""
    target_parent_id = request.data.get('target_parent_id')
    if not target_parent_id:
        return Response({"error": "Нужен target_parent_id"}, status=400)

    connection = UserConnection.objects.filter(
        user1_id=target_parent_id,
        user2=request.user,
        connection_type='parent_request'
    )
    if connection.exists():
        connection.delete()
        return Response({"message": "Запрос отклонен"})
    return Response({"error": "Запрос не найден"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_by_child(request):
    """Ребенок инициирует отвязку (target_parent_id)"""
    target_parent_id = request.data.get('target_parent_id')
    if not target_parent_id:
        return Response({"error": "Нужен target_parent_id"}, status=400)

    connection = UserConnection.objects.filter(
        user1_id=target_parent_id,
        user2=request.user,
        connection_type='parent_child'
    )
    if connection.exists():
        connection.update(
            connection_type='child_request',
            is_child_flag=False
        )
        updated = connection.first()
        return Response({
            "message": "Отвязка инициирована",
            "connection": ConnectionSerializer(updated).data
        })
    return Response({"error": "Активная связь не найдена"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_by_parent(request):
    """Родитель полностью удаляет связь (target_child_id)"""
    target_child_id = request.data.get('target_child_id')
    if not target_child_id:
        return Response({"error": "Нужен target_child_id"}, status=400)

    connections = UserConnection.objects.filter(
        user1=request.user,
        user2_id=target_child_id,
        connection_type__in=['parent_child', 'child_request']
    )
    if connections.exists():
        connections.delete()
        return Response({"message": "Связь удалена"})
    return Response({"error": "Связь не найдена"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_friendship(request):
    """Запрос в друзья (target_user_id)"""
    serializer = ConnectionRequestSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        target_user = User.objects.get(id=serializer.validated_data['target_user_id'])

        # Проверка существующей дружбы
        if UserConnection.objects.filter(
                models.Q(user1=request.user, user2=target_user, connection_type='friendship') |
                models.Q(user1=target_user, user2=request.user, connection_type='friendship')
        ).exists():
            return Response({"error": "Уже друзья"}, status=400)

        # Запрос в друзья
        connection = UserConnection.objects.create(
            user1=request.user,
            user2=target_user,
            connection_type='friendship',
            is_parent_flag=False,  # Не используется для друзей
            is_child_flag=False
        )
        return Response({
            "message": "Запрос в друзья отправлен",
            "connection": ConnectionSerializer(connection).data
        }, status=201)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_friendship(request):
    """Подтверждение дружбы (target_user_id)"""
    target_user_id = request.data.get('target_user_id')
    if not target_user_id:
        return Response({"error": "Нужен target_user_id"}, status=400)

    try:
        connection = UserConnection.objects.get(
            user2=request.user,
            user1_id=target_user_id,
            connection_type='friendship'
        )
        # Для друзей просто активируем связь
        connection.is_parent_flag = True  # Подтверждение получателя
        connection.is_child_flag = True  # Отправитель уже согласился
        connection.save()

        return Response({
            "message": "Теперь вы друзья!",
            "connection": ConnectionSerializer(connection).data
        })
    except UserConnection.DoesNotExist:
        return Response({"error": "Запрос не найден"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_friendship(request):
    """Отклонение запроса в друзья (target_user_id)"""
    target_user_id = request.data.get('target_user_id')
    if not target_user_id:
        return Response({"error": "Нужен target_user_id"}, status=400)

    connections = UserConnection.objects.filter(
        user2=request.user,
        user1_id=target_user_id,
        connection_type='friendship'
    )
    if connections.exists():
        connections.delete()
        return Response({"message": "Запрос отклонен"})
    return Response({"error": "Запрос не найден"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_friend(request):
    """Удаление из друзей (target_user_id) - любой может удалить"""
    target_user_id = request.data.get('target_user_id')
    if not target_user_id:
        return Response({"error": "Нужен target_user_id"}, status=400)

    # Удаляем ВСЕ связи friendship между пользователями
    connections = UserConnection.objects.filter(
        models.Q(
            (models.Q(user1=request.user, user2_id=target_user_id) |
             models.Q(user1_id=target_user_id, user2=request.user)) &
            models.Q(connection_type='friendship')
        )
    )

    if connections.exists():
        deleted_count = connections.count()
        connections.delete()
        return Response({
            "message": f"Удалено {deleted_count} связей дружбы"
        })
    return Response({"error": "Дружба не найдена"}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_friend_requests(request):
    """Запросы в друзья для текущего пользователя"""
    requests = UserConnection.objects.filter(
        user2=request.user,
        connection_type='friendship'
    ).exclude(is_parent_flag=True).select_related('user1')

    serializer = ConnectionSerializer(requests, many=True)
    return Response({
        "friend_requests": serializer.data,
        "pending_count": len(serializer.data)
    })
