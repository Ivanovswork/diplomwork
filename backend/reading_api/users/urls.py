from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegistrUserView.as_view(), name='register'),
    path('confirm-email/<str:key>/', views.confirm_email, name='confirm_email'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('password-reset-request/', views.password_reset_request, name='password_reset_request'),
    path('password-reset-verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password_reset_confirm'),
]