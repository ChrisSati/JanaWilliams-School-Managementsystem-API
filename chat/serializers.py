from rest_framework import serializers
from chat.models import Chat
from users.models import User
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta




class ChatSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    receiver_name = serializers.CharField(source='receiver.username', read_only=True)
    sender_profile_image = serializers.SerializerMethodField()
    receiver_profile_image = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Chat
        fields = [
            'id', 'sender', 'receiver', 'message', 'image', 'timestamp',
            'sender_name', 'sender_profile_image',
            'receiver_name', 'receiver_profile_image'
        ]
        read_only_fields = ['sender']

    def get_sender_profile_image(self, obj):
        request = self.context.get('request')
        if obj.sender.profile_image and hasattr(obj.sender.profile_image, 'url'):
            return request.build_absolute_uri(obj.sender.profile_image.url)
        return None

    def get_receiver_profile_image(self, obj):
        request = self.context.get('request')
        if obj.receiver.profile_image and hasattr(obj.receiver.profile_image, 'url'):
            return request.build_absolute_uri(obj.receiver.profile_image.url)
        return None


class UserListSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()
    last_seen_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type',  'profile_image', 'is_online', 'last_seen_display']

    def get_is_online(self, obj):
        # Return whether the user is currently online
        return obj.is_online

    def get_last_seen_display(self, obj):
        # Don't display anything if user is currently online
        if obj.is_online:
            return None

        # If last_seen is missing, return nothing
        if obj.last_seen is None:
            return None

        time_diff = timezone.now() - obj.last_seen

        if time_diff < timedelta(minutes=1):
            return "Less than a minute ago"
        elif time_diff < timedelta(hours=1):
            minutes = time_diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif time_diff < timedelta(days=1):
            hours = time_diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = time_diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"


