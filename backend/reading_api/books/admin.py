from django.contrib import admin
from .models import UserConnection, Book

class UserConnectionAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'connection_type', 'is_parent_flag']
    list_filter = ['connection_type']
    raw_id_fields = ['user1', 'user2']

@admin.register(UserConnection)
class UserConnectionAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'connection_type', 'is_parent_flag', 'is_child_flag']
    list_filter = ['connection_type']
    raw_id_fields = ['user1', 'user2']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'pages_count', 'status', 'daily_goal', 'upload_date']
    list_filter = ['status', 'upload_date']
    raw_id_fields = ['user']
    readonly_fields = ['pages_count', 'upload_date']
