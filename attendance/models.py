from django.db import models
from django.utils import timezone
from academics.models import GradeClass, StudentAdmission
from users.models import User

class StudentAttendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excuse', 'Excused'),
        ('drop', 'Dropped'),
    )

    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE, related_name="attendance_records")
    grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    taken_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student', 'date')  # Prevent duplicates

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"
