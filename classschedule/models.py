from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, date
from django.utils.translation import gettext_lazy as _

from academics.models import GradeClass, Subject
from teacherdata.models import TeacherDataProcess

# Day choices using IntegerChoices for proper ordering
class DayOfWeek(models.IntegerChoices):
    MONDAY = 1, 'Monday'
    TUESDAY = 2, 'Tuesday'
    WEDNESDAY = 3, 'Wednesday'
    THURSDAY = 4, 'Thursday'
    FRIDAY = 5, 'Friday'

# Period choices using IntegerChoices, including Recess
class PeriodChoices(models.IntegerChoices):
    P1 = 1, '1st Period'
    P2 = 2, '2nd Period'
    P3 = 3, '3rd Period'
    RECESS = 99, 'Recess Period'
    P4 = 4, '4th Period'
    P5 = 5, '5th Period'
    P6 = 6, '6th Period'
    P7 = 7, '7th Period'

class ClassSchedule(models.Model):
    grade_class = models.ForeignKey(
        GradeClass,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherDataProcess, on_delete=models.CASCADE)

    period = models.PositiveSmallIntegerField(choices=PeriodChoices.choices)
    day_of_week = models.PositiveSmallIntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day_of_week', 'period', 'start_time']
        unique_together = [
            ('grade_class', 'day_of_week', 'period'),  # A grade class can't have two lessons in the same period
            ('teacher', 'day_of_week', 'start_time', 'end_time')  # Teacher can't double-book
        ]

    def __str__(self):
        return (
            f"{self.grade_class} - {self.subject} "
            f"({self.get_period_display()}) on {self.get_day_of_week_display()} "
            f"from {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')}"
        )

    def clean(self):
        super().clean()

        # 1. End time must be after start time
        if self.end_time <= self.start_time:
            raise ValidationError(_("End time must be after start time."))

        # 2. Check for overlapping schedules within the same grade class
        class_conflicts = ClassSchedule.objects.filter(
            grade_class=self.grade_class,
            day_of_week=self.day_of_week
        ).exclude(pk=self.pk)

        overlaps = class_conflicts.filter(
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )
        if overlaps.exists():
            raise ValidationError(_("This time overlaps with another schedule for this class."))

        # 3. Check for overlapping schedules for the same teacher
        teacher_conflicts = ClassSchedule.objects.filter(
            teacher=self.teacher,
            day_of_week=self.day_of_week
        ).exclude(pk=self.pk)

        teacher_overlaps = teacher_conflicts.filter(
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )
        if teacher_overlaps.exists():
            raise ValidationError(_("This time overlaps with another schedule for this teacher."))

    @property
    def duration_minutes(self):
        delta = (
            datetime.combine(date.today(), self.end_time)
            - datetime.combine(date.today(), self.start_time)
        )
        return delta.seconds // 60
