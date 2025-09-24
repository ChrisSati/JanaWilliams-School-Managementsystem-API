from rest_framework import serializers
from .models import Notification
from django.utils.timezone import localtime


    



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'title', 'is_read', 'created_at'] 

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Convert to ISO format in UTC
        representation['created_at'] = localtime(instance.created_at).isoformat()
        return representation