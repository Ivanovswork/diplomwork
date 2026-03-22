from django.urls import path
from . import views

urlpatterns = [
    path('read/<int:book_id>/', views.read_book, name='read_book'),
]