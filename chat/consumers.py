import json
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import Chat
from users.models import User
from chatnotification.models import Chatnotification


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.other_user_id = self.scope['url_route']['kwargs'].get('receiver_id')

        print(f"[WebSocket] Connect attempt: user={getattr(self.user, 'id', None)}, receiver_id={self.other_user_id}")

        if not self.user.is_authenticated or self.user.id is None:
            await self.close()
            return

        try:
            self.other_user_id = int(self.other_user_id)
        except (TypeError, ValueError):
            await self.close()
            return

        self.room_group_name = self.get_room_name(self.user.id, self.other_user_id)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        image_url = data.get('image')
        timestamp = data.get('timestamp')  # optional, from frontend after upload

        # If no message and no image, ignore
        if not message and not image_url:
            return

        sender = self.user
        receiver = await self.get_user(self.other_user_id)
        if not receiver:
            return

        sender_image_url = await self.get_profile_image_url(sender)

        # If the message is sent only via WebSocket (no API upload), save it to DB here
        # But if image_url exists, it means image was uploaded via API, so skip saving here
        if not image_url:
            chat = await self.save_chat(sender, receiver, message)
            # Use DB timestamp if available
            timestamp = chat.timestamp.isoformat()
            image_url = None
        else:
            # For image messages, timestamp may come from frontend after upload
            pass

        # Broadcast message to group (both sender and receiver)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender.id,
                'image': image_url,
                'receiver_id': receiver.id,
                'timestamp': timestamp,
                'sender_profile_image': sender_image_url,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    def get_room_name(self, user1, user2):
        user1 = int(user1)
        user2 = int(user2)
        return f"chat_{min(user1, user2)}_{max(user1, user2)}"

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_chat(self, sender, receiver, message):
        chat = Chat.objects.create(sender=sender, receiver=receiver, message=message)
        Chatnotification.objects.create(
            sender=sender,
            receiver=receiver,
            message_preview=message[:100] if message else "[Image]",
            is_read=False
        )
        return chat

    @database_sync_to_async
    def get_profile_image_url(self, user):
        if user.profile_image and hasattr(user.profile_image, 'url'):
            return settings.MEDIA_URL + user.profile_image.name
        return None

