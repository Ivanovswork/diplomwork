from django.urls import path
from . import views

urlpatterns = [
    path('book/<int:book_id>/stats/', views.get_book_stats, name='book_stats'),
    path('session/<int:book_id>/', views.get_or_create_session, name='get_or_create_session'),
    path('page/save/', views.save_page_read, name='save_page_read'),
    path('session/<int:session_id>/continue/', views.continue_reading, name='continue_reading'),
    path('session/<int:session_id>/finish/', views.finish_reading, name='finish_reading'),
    path('streak/', views.get_user_streak, name='user_streak'),
    path('stats/', views.get_reading_stats, name='reading_stats'),
    path('read-web/<int:book_id>/', views.read_book_web, name='read_book_web'),
    path('pdf-proxy/<int:book_id>/', views.pdf_proxy, name='pdf_proxy'),  # ← НОВЫЙ
]