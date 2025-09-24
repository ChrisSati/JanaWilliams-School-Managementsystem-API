from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Chatnotification
from .serializers import ChatNotificationSerializer
from rest_framework.exceptions import NotFound


class ChatnotificationViewSet(viewsets.ModelViewSet):
    queryset = Chatnotification.objects.all()
    serializer_class = ChatNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chatnotification.objects.filter(receiver=self.request.user)

    # Custom action to mark a notification as read
    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        try:
            notification = self.get_object()
            if notification.receiver != request.user:
                raise NotFound('Notification not found or access denied.')
            notification.is_read = True
            notification.save()
            return Response({'status': 'Notification marked as read'}, status=status.HTTP_200_OK)
        except Chatnotification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

    # Custom action to mark a notification as unread
    @action(detail=True, methods=['patch'])
    def mark_as_unread(self, request, pk=None):
        try:
            notification = self.get_object()
            if notification.receiver != request.user:
                raise NotFound('Notification not found or access denied.')
            notification.is_read = False
            notification.save()
            return Response({'status': 'Notification marked as unread'}, status=status.HTTP_200_OK)
        except Chatnotification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
