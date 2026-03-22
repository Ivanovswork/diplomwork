from rest_framework import serializers
from users.models import User
from users.serializers import UserSerializer
from .models import UserConnection


class ConnectionRequestSerializer(serializers.Serializer):
    target_user_id = serializers.IntegerField()

    def validate_target_user_id(self, value):
        request = self.context['request']
        if value == request.user.id:
            raise serializers.ValidationError("Нельзя привязать самого себя")
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Пользователь не найден")
        return value


class ConnectionSerializer(serializers.ModelSerializer):
    user1_data = UserSerializer(source='user1', read_only=True)
    user2_data = UserSerializer(source='user2', read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = UserConnection
        fields = ['id', 'user1_data', 'user2_data', 'connection_type',
                  'is_parent_flag', 'is_child_flag', 'status']

    def get_status(self, obj):
        if obj.connection_type == 'parent_child': return 'active'
        if obj.connection_type == 'parent_request': return 'parent_pending'
        if obj.connection_type == 'child_request': return 'child_pending'
        return 'pending'
