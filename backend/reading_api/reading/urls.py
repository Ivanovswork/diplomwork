from django.urls import path
from . import views

urlpatterns = [
    path('session/<int:book_id>/', views.get_book_session),
    path('session/start/', views.start_session),
    path('page/next/', views.next_page),
    path('test/<int:session_id>/', views.get_test),
    path('page/<int:book_id>/<int:page_num>/', views.get_single_page),
]