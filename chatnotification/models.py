from django.db import models
from users.models import User
from django.utils import timezone

class Chatnotification(models.Model):
    receiver = models.ForeignKey(User, related_name='chatnotifications', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='chatsent_notifications', on_delete=models.CASCADE)
    message_preview = models.CharField(max_length=100)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def sender_name(self):
        """Returns the full name of the sender."""
        return self.sender.username

    def sender_profile_image_url(self):
        """Returns the URL of the sender's profile image."""
        return self.sender.profile_image.url if self.sender.profile_image else None

    def __str__(self):
        """Returns a string representation of the notification."""
        return f"Notification to {self.receiver.username} from {self.sender.username}"

    class Meta:
        """Ordering by timestamp for fetching recent notifications first."""
        ordering = ['-timestamp']
