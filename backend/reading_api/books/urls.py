from django.urls import path
from . import views

urlpatterns = [
    # Родители
    # Списки
    path('connections/', views.list_my_connections, name='my_connections'),
    path('connections/parent-requests/', views.list_parent_requests, name='parent_requests'),

    # Привязка
    path('connections/request/', views.request_parent_connection, name='request_parent'),
    path('connections/confirm/', views.confirm_connection, name='confirm'),
    path('connections/reject/', views.reject_connection, name='reject'),

    # Отвязка
    path('connections/unlink-child/', views.unlink_by_child, name='unlink_child'),
    path('connections/unlink-parent/', views.unlink_by_parent, name='unlink_parent'),

    # Друзья
    path('friends/request/', views.request_friendship, name='friend_request'),
    path('friends/confirm/', views.confirm_friendship, name='confirm_friend'),
    path('friends/reject/', views.reject_friendship, name='reject_friend'),
    path('friends/remove/', views.remove_friend, name='remove_friend'),
    path('friends/requests/', views.list_friend_requests, name='friend_requests'),
]