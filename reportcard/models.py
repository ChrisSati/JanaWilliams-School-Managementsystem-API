from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Avg, F, Window
from django.db.models.functions import Rank
from academics.models import GradeClass, StudentAdmission, Subject
from notifications.models import Notification
from users.models import User 
from academicyear.models import AcademicYear
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class Period(models.Model):
    PERIOD_CHOICES = [
        ('Period 1', 'Period 1'),
        ('Period 2', 'Period 2'),
        ('Period 3', 'Period 3'),
        ('Exam', 'Exam'),
        ('Period 4', 'Period 4'),
        ('Period 5', 'Period 5'),
        ('Period 6', 'Period 6'),
        ('Examm', 'Examm'),
    ]
    name = models.CharField(max_length=100, choices=PERIOD_CHOICES, unique=True)

    def __str__(self):
        return self.name

class GradeDistribution(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentAdmission, related_name='grade_distributions', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    quiz_score = models.FloatField(default=0)
    assignment_score = models.FloatField(default=0)
    participation_score = models.FloatField(default=0)
    test_score = models.FloatField(default=0)
    allow_teacher_update = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.academic_year_id:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if not active_year:
                raise ValidationError("No active Academic Year set. Please activate one.")
            self.academic_year = active_year
        super().save(*args, **kwargs)
   

    def final_score(self):
        return self.quiz_score + self.assignment_score + self.participation_score + self.test_score

    def formatted_final_score(self):
        score = self.final_score()
        # Return just the raw score (float)
        return score

    def get_remark(self):
        score = self.final_score()
        if score < 60:
            return "Needs Serious Improvement"
        elif 60 <= score <= 69:
            return "Need Improvement"
        elif 70 <= score <= 79:
            return "You can do better than this"
        elif 80 <= score <= 84:
            return "Very Good"
        elif 85 <= score <= 89:
            return "Very Very Good"
        elif 90 <= score <= 100:
            return "Excitement - Principal List"
        return "Invalid Score"

    @staticmethod
    def rank_students(grade_class, period, student):
        ranked_students = (GradeDistribution.objects
            .filter(grade_class=grade_class, period=period)
            .annotate(final_score_value=F('quiz_score') + F('assignment_score') + F('participation_score') + F('test_score'))
            .annotate(rank=Window(expression=Rank(), order_by=F('final_score_value').desc()))
        )
        student_rank = ranked_students.filter(student=student).values_list('rank', flat=True).first()
        return student_rank if student_rank else "N/A"

    def clean(self):
        if self.student.grade_class != self.grade_class:
            raise ValidationError(f"Student {self.student} does not belong to Grade Class {self.grade_class}.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.subject} ({self.grade_class})"

class StudentAverage(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)  # NEW
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE)
    grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    published = models.BooleanField(default=False)  # Field to track if grades are published

    def save(self, *args, **kwargs):
        if not self.academic_year_id:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if not active_year:
                raise ValidationError("No active Academic Year set. Please activate one.")
            self.academic_year = active_year
        super().save(*args, **kwargs)

    def student_subjects(self):
        distributions = GradeDistribution.objects.filter(student=self.student, period=self.period)
        return [
            {
                'subject_name': distribution.subject.name,
                'formatted_final_score': distribution.formatted_final_score()
            }
            for distribution in distributions
        ]

    def average_score(self):
        avg_score = GradeDistribution.objects.filter(
            student=self.student,
            period=self.period 
        ).aggregate(
            avg=Avg(
                F('quiz_score') + F('assignment_score') + F('participation_score') + F('test_score')
            )
        )['avg'] or 0
        return avg_score

    def formatted_average_score(self):
        avg_score = self.average_score() or 0  
        # Return raw float rounded to 2 decimals
        return round(avg_score, 2)

    def get_remark(self):
        avg_score = self.average_score()
        if avg_score < 60:
            return "Needs Serious Improvement"
        elif 60 <= avg_score <= 69:
            return "Need Improvement"
        elif 70 <= avg_score <= 79:
            return "You can do better than this"
        elif 80 <= avg_score <= 84:
            return "Very Good"
        elif 85 <= avg_score <= 89:
            return "Very Very Good"
        elif 90 <= avg_score <= 100:
            return "Excitement - Principal List"
        return "Invalid Score"

    @staticmethod
    def rank_students(grade_class):
        ranked_students = (
            StudentAverage.objects
            .filter(grade_class=grade_class)
            .values('student')  
            .annotate(
                avg_score=Avg(
                    F('student__grade_distributions__quiz_score') +
                    F('student__grade_distributions__assignment_score') +
                    F('student__grade_distributions__participation_score') +
                    F('student__grade_distributions__test_score')
                )
            )
            .order_by('-avg_score')  
        )

        ranked_list = []
        current_rank = 1
        for student in ranked_students:
            student['rank'] = current_rank
            ranked_list.append(student)
            current_rank += 1

        return ranked_list

    def publish(self):
        self.published = True
        self.save()

        # Create notifications for students when grades are published
        students = User.objects.filter(user_type='student')
        for student in students:
            Notification.objects.create(
                user=student,
                message=f"Grades for {self.period.name} have been published. Check Your Grade Report."
            )

class GradesReport(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)  # NEW
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE)
    grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE)
    is_published = models.BooleanField(default=False)


    def save(self, *args, **kwargs):
        if not self.academic_year_id:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if not active_year:
                raise ValidationError("No active Academic Year set. Please activate one.")
            self.academic_year = active_year
        super().save(*args, **kwargs)


    def get_student_grades(self):
        """Fetch subjects, final scores, and period averages from GradeDistribution."""
        distributions = GradeDistribution.objects.filter(student=self.student)
        grades = [
            {
                'subject_name': distribution.subject.name,
                'period_name': distribution.period.name,
                'formatted_final_score': distribution.formatted_final_score(),
                'period_average': self.period_average(distribution.period.name)  # Add period average here
            }
            for distribution in distributions
        ]
        return grades

    def period_average(self, period_name):
        """Calculate the average score for a given period."""
        try:
            period = Period.objects.get(name=period_name)
            avg_score = GradeDistribution.objects.filter(
                student=self.student, 
                period=period
            ).aggregate(
                avg=Avg(F('quiz_score') + F('assignment_score') + F('participation_score') + F('test_score'))
            )['avg'] or 0

            avg_score = round(float(avg_score), 2)  
            return avg_score
        except Period.DoesNotExist:
            return "Invalid Period"

    def semester_average(self, semester_number):
        """Calculate average score for a given semester based on period names."""
        semester_periods = Period.objects.filter(name__in=[f'Period {i}' for i in range(1 + (semester_number - 1) * 3, semester_number * 3 + 1)] + ['Exam']).values_list('id', flat=True)

        semester_avg = GradeDistribution.objects.filter(
            student=self.student, 
            period_id__in=semester_periods
        ).aggregate(
            avg=Avg(F('quiz_score') + F('assignment_score') + F('participation_score') + F('test_score'))
        )['avg'] or 0

        return semester_avg

    def yearly_average(self):
        """Calculate yearly average based on semester averages."""
        first_semester_avg = self.semester_average(1)
        second_semester_avg = self.semester_average(2)

        yearly_avg = (first_semester_avg + second_semester_avg) / 2
        return yearly_avg

    def get_semester_rank(self, semester_number):
        """Get the rank of the student in the specified semester."""
        semester_avg = self.semester_average(semester_number)
        all_students = GradesReport.objects.filter(grade_class=self.grade_class)
        ranked_students = all_students.annotate(
            avg=Avg(F('student__grade_distributions__quiz_score') + F('student__grade_distributions__assignment_score') +
                    F('student__grade_distributions__participation_score') + F('student__grade_distributions__test_score'))
        ).order_by('-avg')

        rank = next((index + 1 for index, report in enumerate(ranked_students) if report.student == self.student), None)
        return rank
    
    def get_yearly_rank(self):
        """Get the rank of the student based on the yearly average."""
        yearly_avg = self.yearly_average()
        all_students = GradesReport.objects.filter(grade_class=self.grade_class)

        ranked_students = (
            all_students
            .values('student')  
            .annotate(
                avg=Avg(
                    F('student__grade_distributions__quiz_score') +
                    F('student__grade_distributions__assignment_score') +
                    F('student__grade_distributions__participation_score') +
                    F('student__grade_distributions__test_score')
                )
            )
            .order_by('-avg')  
        )

        rank = None
        for index, student in enumerate(ranked_students, start=1):
            if student['student'] == self.student.id:
                rank = index
                break

        return rank

    def get_remark(self):
        """Determine remark based on yearly average."""
        yearly_avg = self.yearly_average()
        if yearly_avg < 60:
            return "Needs Serious Improvement"
        elif 60 <= yearly_avg <= 69:
            return "Need Improvement"
        elif 70 <= yearly_avg <= 79:
            return "You can do better than this"
        elif 80 <= yearly_avg <= 84:
            return "Very Good"
        elif 85 <= yearly_avg <= 89:
            return "Very Very Good"
        elif 90 <= yearly_avg <= 100:
            return "Excitement - Principal List"
        return "Invalid Score"

    def __str__(self):
        return f"{self.student} - Grades Report"

