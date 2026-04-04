from django.urls import path
from . import views

urlpatterns = [
    # Статистика книги
    path('book/<int:book_id>/stats/', views.get_book_stats, name='book_stats'),
    path('book/<int:book_id>/stats-with-daily/', views.get_book_stats_with_daily_goal, name='book_stats_with_daily'),
    path('book/<int:book_id>/test-stats/', views.get_book_test_stats, name='book_test_stats'),

    # Сессии
    path('session/<int:book_id>/', views.get_or_create_session, name='get_or_create_session'),
    path('session/<int:session_id>/continue/', views.continue_reading, name='continue_reading'),
    path('session/<int:session_id>/finish/', views.finish_reading, name='finish_reading'),

    # Страницы
    path('page/save/', views.save_page_read, name='save_page_read'),
    path('pdf-proxy/<int:book_id>/', views.pdf_proxy, name='pdf_proxy'),
    path('read-web/<int:book_id>/', views.read_book_web, name='read_book_web'),

    # Тесты
    path('test/<int:test_id>/', views.get_test, name='get_test'),
    path('test/<int:test_id>/submit/', views.submit_test, name='submit_test'),
    path('test/<int:test_id>/retake/', views.retake_test, name='retake_test'),
    path('test/check/<int:session_id>/', views.check_test_required, name='check_test_required'),

    # Стрик и статистика
    path('streak/', views.get_user_streak, name='user_streak'),
    path('stats/', views.get_reading_stats, name='reading_stats'),
    path('block/<int:book_id>/<int:block_number>/', views.get_block_text, name='block_text'),

    path('child/<int:child_id>/full-stats/', views.get_child_full_stats, name='child_full_stats'),
    path('child/<int:child_id>/book/<int:book_id>/stats/', views.get_child_book_stats, name='child_book_stats'),
]