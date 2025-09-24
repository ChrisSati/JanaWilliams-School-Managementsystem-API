from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import re

# Custom validator to allow spaces in usernames
def custom_username_validator(username):
    if not re.match(r'^[\w.@+\- ]+$', username):
        raise ValidationError("Username can only contain letters, numbers, spaces, and @/./+/-/_ characters.")

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'), #done
        ('teacher', 'Teacher'), #done
        ('parent', 'Parent'), #done
        ('student', 'Student'), #done
        ('registry', 'Registry'), #done
        ('business manager', 'Business Manager'), #done
        ('vpi', 'VPI'), #done
        ('vpa', 'VPA'), #done
        ('dean', 'Dean'),
        ('it personel', 'IT Personnel'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    # Extra profile fields
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='admin')
    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png', 'jpeg'])]
    )

    # Use email as login field
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[custom_username_validator],
    )

    # Online tracking
    last_seen = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)  # ✅ For real-time online status

    # Required config
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Email is already required by USERNAME_FIELD

    def __str__(self):
        return self.username

