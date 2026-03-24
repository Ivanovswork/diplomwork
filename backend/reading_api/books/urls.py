from django.urls import path
from . import views

urlpatterns = [
    # Общие связи
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

    # Друзья
    path('friends/', views.list_friends, name='list_friends'),
    path('friends/requests/', views.list_friend_requests, name='friend_requests'),
    path('friends/request/', views.request_friendship, name='friend_request'),
    path('friends/confirm/', views.confirm_friendship, name='confirm_friend'),
    path('friends/reject/', views.reject_friendship, name='reject_friend'),
    path('friends/remove/', views.remove_friend, name='remove_friend'),
    path('friends/add-by-email/', views.add_friend_by_email, name='add_friend_by_email'),

    # Родительский контроль
    path('parent/children/', views.list_children, name='list_children'),
    path('parent/parents/', views.list_parents, name='list_parents'),
    path('parent/request-by-email/', views.request_parent_by_email, name='request_parent_by_email'),

    # Книги
    path('books/', views.upload_book, name='upload_book'),
    path('books/child/', views.upload_book_to_child, name='upload_book_child'),
    path('books/my/', views.list_my_books, name='my_books'),
    path('books/child/<int:child_id>/', views.list_child_books, name='child_books'),
    path('books/<int:book_id>/', views.get_book_details, name='book_details'),
    path('books/<int:book_id>/daily-goal/', views.update_book_daily_goal, name='update_daily_goal'),
    path('books/<int:book_id>/delete/', views.delete_book, name='delete_book'),
    path('books/limit/', views.get_book_limit, name='book_limit'),
    path('books/child-limit/<int:child_id>/', views.get_child_book_limit, name='child_book_limit'),
    path('stats/', views.get_user_stats, name='user_stats'),
]