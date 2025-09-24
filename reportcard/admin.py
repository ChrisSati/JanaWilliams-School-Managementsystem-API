
from django.contrib import admin
from django.utils.html import format_html
from django.db.models.functions import Rank
from django.db.models import F, Avg, Window
from reportcard.forms import GradeDistributionForm
from academics.models import StudentAdmission
from .models import GradeDistribution, GradesReport, StudentAverage, Period
from django.http import JsonResponse
from django.urls import path
from .models import StudentAverage, GradeDistribution, StudentAdmission



class PeriodAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    # list_filter = ('name')

admin.site.register(Period, PeriodAdmin)

class GradeDistributionAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'grade_class', 'subject', 'period', 'quiz_score', 'formatted_final_score', 'get_remark')
    list_filter = ('grade_class', 'period', 'subject')

admin.site.register(GradeDistribution, GradeDistributionAdmin)





class StudentAverageAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'period', 'student', 'grade_class', 'student_rank', 
        'display_subjects_scores', 'formatted_average_score', 'get_remark', 'published'
    )
    list_filter = ('grade_class', 'student', 'published')
    search_fields = ('student__first_name', 'student__last_name', 'grade_class__name', 'period__name')
    ordering = ('-period', 'grade_class')
    actions = ['publish_grades', 'unpublish_grades']

    def display_subjects_scores(self, obj):
        """Displays subjects with their final scores for a student in a given period."""
        subjects = GradeDistribution.objects.filter(student=obj.student, period=obj.period)
        subject_scores = [
            f"<strong>{subject.subject.name}:</strong> {self.format_score(subject.final_score())}"
            for subject in subjects
        ]
        return format_html("<br>".join(subject_scores)) if subject_scores else "No scores available"

    display_subjects_scores.short_description = "Subjects & Final Scores"

    def format_score(self, score):
        """Formats the score, highlighting in red if below 70."""
        if score is None:
            return "N/A"
        if score < 70:
            return format_html('<span style="color: red;">{}</span>', score)
        return score

    def formatted_average_score(self, obj):
        """Calculates and displays the formatted average score for the student in the given period."""
        scores = GradeDistribution.objects.filter(student=obj.student, period=obj.period)
        average_score = scores.aggregate(avg_score=Avg(
            F('quiz_score') + F('assignment_score') + F('participation_score') + F('test_score')
        ))['avg_score']

        if average_score is not None:
            return self.format_score(round(average_score, 2))
        return "N/A"

    formatted_average_score.short_description = "Formatted Avg Score"

    def student_rank(self, obj):
        """Calculates and returns the student's rank based on final scores within the grade class for the period."""
        ranked_students = (
            GradeDistribution.objects.filter(grade_class=obj.grade_class, period=obj.period)
            .values('student')
            .annotate(final_score_value=Avg(
                F('quiz_score') + F('assignment_score') + F('participation_score') + F('test_score')
            ))
            .annotate(rank=Window(expression=Rank(), order_by=F('final_score_value').desc()))
        )

        # Find the rank for the specific student
        for student in ranked_students:
            if student['student'] == obj.student.id:
                return student['rank']
        return "N/A"

    student_rank.short_description = "Rank"

    @admin.action(description='Publish selected grades')
    def publish_grades(self, request, queryset):
        updated = queryset.update(published=True)
        self.message_user(request, f'{updated} grade(s) published successfully.')

    @admin.action(description='Unpublish selected grades')
    def unpublish_grades(self, request, queryset):
        updated = queryset.update(published=False)
        self.message_user(request, f'{updated} grade(s) unpublished successfully.')

admin.site.register(StudentAverage, StudentAverageAdmin)



class GradesReportAdmin(admin.ModelAdmin):  
    list_display = (
        'student',
        'grade_class',
        'get_period_averages',  
        'get_student_subjects',  
        'first_semester_average_display',
        'second_semester_average_display',
        'yearly_average_display',
        'get_yearly_rank',
        'get_remark'
    )

    def get_student_subjects(self, obj):
        """Display subject names and formatted scores, grouped by period."""
        subjects = obj.get_student_grades()
        subjects_by_period = {}

     
        for sub in subjects:
            period_name = sub['period_name']
            if period_name not in subjects_by_period:
                subjects_by_period[period_name] = []
            subjects_by_period[period_name].append(f"{sub['subject_name']}: {sub['formatted_final_score']}")

    
        formatted_subjects = []
        for period, subjects in subjects_by_period.items():
            formatted_subjects.append(f"{period}:<br>" + "<br>".join(subjects))
        
        return format_html("<br><br>".join(formatted_subjects))

    get_student_subjects.short_description = "Subjects and Scores by Period"

    def first_semester_average_display(self, obj):
        """Display the formatted first semester average."""
        first_semester_avg = obj.semester_average(1)
        if first_semester_avg < 70:
            return format_html('<span style="color: red;">{}</span>', first_semester_avg)
        return first_semester_avg

    first_semester_average_display.short_description = "First Semester Average"

    def second_semester_average_display(self, obj):
        """Display the formatted second semester average."""
        second_semester_avg = obj.semester_average(2)
        if second_semester_avg < 70:
            return format_html('<span style="color: red;">{}</span>', second_semester_avg)
        return second_semester_avg

    second_semester_average_display.short_description = "Second Semester Average"

    def yearly_average_display(self, obj):
        """Display the formatted yearly average."""
        yearly_avg = obj.yearly_average()
        if yearly_avg < 70:
            return format_html('<span style="color: red;">{}</span>', yearly_avg)
        return yearly_avg

    def get_period_averages(self, obj):
        """Display the average scores for each period."""
        periods = Period.objects.all()  
        period_averages = []

        for period in periods:
            avg_score = obj.period_average(period.name) 
            period_averages.append(f"{period.name}: {avg_score}")
        
        return format_html("<br>".join(period_averages))

    get_period_averages.short_description = "Period Averages"

    def get_yearly_rank(self, obj):
        """Display the rank of the student based on yearly average."""
        rank = obj.get_yearly_rank()
        return rank if rank is not None else "N/A"

    get_student_subjects.short_description = "Subjects and Scores by Period"

admin.site.register(GradesReport, GradesReportAdmin)



