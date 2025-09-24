from django.db import models
from django.core.exceptions import ValidationError
from academics.models import StudentAdmission   
from users.models import User


def validate_complaint_poster(user):
    allowed_roles = ['admin', 'teacher', 'registry', 'business manager', 'vpi', 'vpa', 'dean']
    if user.user_type not in allowed_roles:
        raise ValidationError(
            f"User of type '{user.user_type}' is not allowed to post complaints."
        )


class Complaint(models.Model):
    poster = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posted_complaints',
        help_text="User (Admin/Teacher/etc.) who posted the complaint",
    )
    student = models.ForeignKey(
        StudentAdmission,
        on_delete=models.CASCADE,
        related_name='complaints',
        help_text="The student this complaint is about",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        validate_complaint_poster(self.poster)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Complaint about {self.student.full_name} - {self.title}"
