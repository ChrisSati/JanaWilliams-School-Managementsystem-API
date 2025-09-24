from django.db.models import Q
from rest_framework import generics
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from chatnotification.models import Chatnotification
from .models import Chat
from .serializers import ChatSerializer, UserListSerializer

from users.models import User



class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        """Pass the request context to the serializer to handle file/image uploads and access the user."""
        return {'request': self.request}

    def perform_create(self, serializer):
        """
        Automatically set the sender to the logged-in user and create a notification
        for the receiver if they are not the sender.
        """
        chat = serializer.save(sender=self.request.user)

        receiver = chat.receiver
        if receiver != chat.sender:
            Chatnotification.objects.create(
                sender=chat.sender,
                receiver=chat.receiver,
                message_preview=chat.message[:100] if chat.message else "[Image]",
                is_read=False
            )

    @action(detail=True, methods=['get'])
    def chat_history(self, request, pk=None):
        """Retrieve chat history between the logged-in user and another user."""
        try:
            other_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        chats = Chat.objects.filter(
            Q(sender=request.user, receiver=other_user) |
            Q(sender=other_user, receiver=request.user)
        ).order_by('timestamp')

        serializer = self.get_serializer(chats, many=True)
        return Response(serializer.data)


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer 
