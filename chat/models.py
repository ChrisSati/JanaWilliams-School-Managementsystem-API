from django.db import models
from users.models import User


class Chat(models.Model):
    sender = models.ForeignKey(User, related_name='sent_chats', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_chats', on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)  # Text message is optional
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)  # Optional image upload
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

   
    def __str__(self):
        return f"Chat from {self.sender.username} to {self.receiver.username}: {self.message[:50] if self.message else '[Image]'}"

    def sender_profile_image(self):
        return self.sender.profile_image.url if self.sender.profile_image else None

    def receiver_profile_image(self):
        return self.receiver.profile_image.url if self.receiver.profile_image else None



