from django.urls import path
from . import views

urlpatterns = [
    path('connections/', views.list_my_connections, name='my_connections'),
    path('connections/parent-requests/', views.list_parent_requests, name='parent_requests'),
    path('connections/request/', views.request_parent_connection, name='request_parent'),
    path('connections/confirm/', views.confirm_connection, name='confirm_parent'),
    path('connections/reject/', views.reject_connection, name='reject_parent'),
    path('connections/unlink-child/', views.unlink_by_child, name='unlink_child'),
    path('connections/unlink-parent/', views.unlink_by_parent, name='unlink_parent'),
    path('connections/requests-count/', views.get_requests_count, name='requests_count'),
    path('connections/unlink-requests/', views.list_unlink_requests, name='unlink_requests'),
    path('connections/confirm-unlink/', views.confirm_unlink, name='confirm_unlink'),
    path('connections/reject-unlink/', views.reject_unlink, name='reject_unlink'),

    path('friends/', views.list_friends, name='list_friends'),
    path('friends/requests/', views.list_friend_requests, name='friend_requests'),
    path('friends/request/', views.request_friendship, name='friend_request'),
    path('friends/confirm/', views.confirm_friendship, name='confirm_friend'),
    path('friends/reject/', views.reject_friendship, name='reject_friend'),
    path('friends/remove/', views.remove_friend, name='remove_friend'),
    path('friends/add-by-email/', views.add_friend_by_email, name='add_friend_by_email'),

    path('parent/children/', views.list_children, name='list_children'),
    path('parent/parents/', views.list_parents, name='list_parents'),
    path('parent/request-by-email/', views.request_parent_by_email, name='request_parent_by_email'),
]