from django.db import models
from django.utils import timezone
from users.models import User




NOTIFICATION_TYPES = [
    ('grade_published', 'Grade Published'),
    ('message_received', 'Message Received'),
    ('assignment_due', 'Assignment Due'),
    ('general', 'General'),
    # Add more notification types here
]

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    url = models.URLField(null=True, blank=True)  # Optional URL to direct the user to more info or a specific page

    def __str__(self):
        return f"Notification for {self.user.username}"

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    # Method to create a grade-published notification
    @classmethod
    def create_grade_notification(cls, user, period_name):
        message = f"Your grades for {period_name} have been published. Check Your Grade Report."
        return cls.objects.create(user=user, message=message, type='grade_published')

    # Method to create a general notification
    @classmethod    
    def create_general_notification(cls, user, message):
        return cls.objects.create(user=user, message=message, type='general')
