# notifications/serializers.py


from rest_framework import serializers
from .models import Chatnotification

class ChatNotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Chatnotification
        fields = ['id', 'receiver', 'sender', 'message_preview', 'is_read', 'timestamp', 'sender_name', 'sender_profile_image_url']

    def get_sender_profile_image_url(self, obj):
        request = self.context.get('request')
        if obj.sender.profile_image:
            return request.build_absolute_uri(obj.sender.profile_image.url)
        return None
