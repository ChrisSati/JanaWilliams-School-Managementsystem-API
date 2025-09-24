from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Student

@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'student':
        # Create a new Student profile for the newly created student user
        Student.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_student_profile(sender, instance, **kwargs):
    if instance.user_type == 'student':
        # Save the student's profile if it exists
        instance.student.save()
