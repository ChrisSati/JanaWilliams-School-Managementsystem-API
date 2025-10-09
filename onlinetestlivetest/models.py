from django.db import models
from django.conf import settings
from academics.models import GradeClass, StudentAdmission, Subject
from reportcard.models import Period
from teacherdata.models import TeacherDataProcess

from django.utils import timezone
from users.models import User


class TestAttachment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='test_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-uploaded_at']


class Assignment(models.Model):
    """An assignment posted by a teacher for a grade class & subject."""
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='online_test_assignments'  # matches your existing related_name
    )
    grade_class = models.ForeignKey(
        GradeClass,
        on_delete=models.CASCADE,
        related_name='online_test_assignments'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    file = models.FileField(upload_to='assignments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    # Convenience props (safe deref)
    @property
    def teacher_name(self):
        return getattr(self.teacher, 'full_name', str(self.teacher))

    @property
    def subject_name(self):
        return getattr(self.subject, 'name', str(self.subject))

    @property
    def grade_class_name(self):
        return getattr(self.grade_class, 'name', str(self.grade_class))


class AssignmentLike(models.Model):
    """A user like on an assignment (1 per user)."""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assignment', 'user')
        ordering = ['-created_at']

    def __str__(self):  # pragma: no cover - debug convenience
        return f"{self.user} ? {self.assignment}"


class AssignmentComment(models.Model):
    """Nested comments; a reply is a comment w/ parent."""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):  # pragma: no cover
        return f"Comment by {self.user} on {self.assignment}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            self.is_edited = True
        super().save(*args, **kwargs)








QUESTION_TYPE_CHOICES = (
    ('fill_blank', 'Fill in the Blanks'),
    ('multiple_choice', 'Multiple Choice'),
    ('essay', 'Essay'),
    ('paragraph', 'Paragraph Writing'),
    ('drawing', 'Drawing / Graph'),
)


class PeriodicTest(models.Model):
    direction = models.CharField(max_length=150)
    grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE, related_name='tests')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='tests')
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name='tests')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tests')
              

    start_time = models.DateTimeField(help_text="When the test becomes available")
    end_time = models.DateTimeField(help_text="When the test closes")
    duration = models.DurationField(help_text="Allowed time for completing the test (e.g., 1:30:00)", blank=True, null=True)

    total_marks = models.PositiveIntegerField(default=0)  # Auto-calculated
    created_at = models.DateTimeField(auto_now_add=True)

    def update_total_marks(self):
        total = sum(section.allocated_marks for section in self.sections.all())
        self.total_marks = total
        self.save()

    def __str__(self):
        return f"{self.direction} - {self.grade_class.name} ({self.subject.name})"

    @property
    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            # Calculate duration as timedelta
            self.duration = self.end_time - self.start_time
        super().save(*args, **kwargs)


class TestSection(models.Model):
    test = models.ForeignKey(PeriodicTest, on_delete=models.CASCADE, related_name='sections')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    allocated_marks = models.PositiveIntegerField()
    number_of_questions = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.get_question_type_display()} - {self.allocated_marks} pts"


class Question(models.Model):
    section = models.ForeignKey(TestSection, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_image = models.ImageField(upload_to='test_questions/', blank=True, null=True)
    attachment = models.FileField(upload_to='question_files/', blank=True, null=True)
    structured_payload = models.JSONField(blank=True, null=True)
    marks = models.FloatField(default=1)

    option_a = models.CharField(max_length=255, blank=True, null=True)
    option_b = models.CharField(max_length=255, blank=True, null=True)
    option_c = models.CharField(max_length=255, blank=True, null=True)
    option_d = models.CharField(max_length=255, blank=True, null=True)
    correct_answer = models.CharField(max_length=20, blank=True, null=True)
    

    def __str__(self):
        return f"Q: {self.question_text[:50]}"


class StudentAnswer(models.Model):
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text_answer = models.TextField(blank=True, null=True)
    answer_image = models.ImageField(upload_to='student_answers/', blank=True, null=True)
    structured_response = models.JSONField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks_obtained = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Answer by {self.student} for Question {self.question.id}"









# ///Not Used but Reselve///
class OnlineTest(models.Model):
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_online_tests'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='online_tests'
    )
    grade_class = models.ForeignKey(
        GradeClass,
        on_delete=models.CASCADE,
        related_name='online_tests'
    )
    title = models.CharField(max_length=255)
    duration_minutes = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TestQuestion(models.Model):
    online_test = models.ForeignKey(
        OnlineTest,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
        ]
    )

    def __str__(self):
        return f"Q: {self.question_text[:50]}" 