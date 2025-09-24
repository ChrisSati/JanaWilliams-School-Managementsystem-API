from rest_framework import serializers

from academics.models import StudentAdmission
from .models import GradeDistribution, GradesReport, Period, StudentAverage
from django.db.models import F, Window
from django.db.models.functions import Rank

class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = ['id', 'name']

class GradeDistributionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    grade_class_name = serializers.CharField(source="grade_class.name", read_only=True)  
    subject_name = serializers.CharField(source="subject.name", read_only=True)  
    final_score = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    period_name = serializers.CharField(source='period.name', read_only=True)
    remark = serializers.SerializerMethodField()
    academic_year = serializers.CharField(source="academic_year.name", read_only=True)  # ? read-only

    class Meta:
        model = GradeDistribution
        fields = [
            "id",
            "student",
            "student_name",
            "grade_class",  
            "grade_class_name",  
            "subject",
            "subject_name",
            "period",
            "period_name",
            "quiz_score",
            "assignment_score",
            "participation_score",
            "test_score",
            "final_score",
            "rank",
            "remark",
            "allow_teacher_update",
            "academic_year",  # ? included in output
        ]

    def create(self, validated_data):
        from academicyear.models import AcademicYear
        active_year = AcademicYear.objects.filter(is_active=True).first()
        if not active_year:
            raise serializers.ValidationError("No active academic year found.")
        validated_data["academic_year"] = active_year
        return super().create(validated_data)
    def get_final_score(self, obj):
        return obj.final_score()

    def get_rank(self, obj):
        """Get student's rank within the selected grade_class and period."""
        grade_class = obj.grade_class
        period = obj.period
        student = obj.student

        ranked_students = (
            GradeDistribution.objects.filter(grade_class=grade_class, period=period)
            .annotate(final_score_value=F("quiz_score") + F("assignment_score") + F("participation_score") + F("test_score"))
            .annotate(rank=Window(expression=Rank(), order_by=F("final_score_value").desc()))
        )

        student_rank = ranked_students.filter(student=student).values_list("rank", flat=True).first()
        return student_rank if student_rank else "N/A"

    def get_remark(self, obj):
        score = obj.final_score()
        if score < 70:
            return "Needs Improvement"
        elif 70 <= score < 80:
            return "You can do better than this"
        elif 80 <= score < 85:
            return "Very Good"
        elif 85 <= score < 90:
            return "Very Very Good"
        elif 90 <= score <= 100:
            return "Excellent Principal List"
        return "N/A"



class StudentGradeChartSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name')
    period_name = serializers.CharField(source='period.name')
    final_score = serializers.SerializerMethodField()

    class Meta:
        model = GradeDistribution
        fields = ['subject_name', 'period_name', 'final_score']

    def get_final_score(self, obj):
        return obj.quiz_score + obj.assignment_score + obj.participation_score + obj.test_score




class StudentAverageSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)
    average_score = serializers.SerializerMethodField(read_only=True)
    period_name = serializers.CharField(source='period.name', read_only=True)
    remark = serializers.CharField(source='get_remark', read_only=True)
    rank = serializers.SerializerMethodField()
    student_subjects = serializers.SerializerMethodField()  
    academic_year = serializers.CharField(source="academic_year.name", read_only=True)  # ? read-only

    class Meta:
        model = StudentAverage
        fields = [
            'student', 'student_name', 
            'grade_class', 'grade_class_name', 
            'period', 'period_name',
            'average_score', 'remark', 
            'rank', 'student_subjects',
            'published', 'academic_year'
        ]

    def create(self, validated_data):
        from academicyear.models import AcademicYear
        active_year = AcademicYear.objects.filter(is_active=True).first()
        if not active_year:
            raise serializers.ValidationError("No active academic year found.")
        validated_data["academic_year"] = active_year
        return super().create(validated_data)
    def get_average_score(self, obj):
        return obj.average_score()  

    def get_rank(self, obj):
        grade_class = obj.grade_class
        ranked_students = StudentAverage.rank_students(grade_class)
        for student in ranked_students:
            if student['student'] == obj.student.id:
                return student['rank']
        return None

    def get_student_subjects(self, obj):
        return obj.student_subjects()  

class GradesReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)
    period_average = serializers.SerializerMethodField() 
    yearly_average = serializers.SerializerMethodField()
    semester_1_avg = serializers.SerializerMethodField()  
    semester_2_avg = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    period_grades = serializers.SerializerMethodField()
    remark = serializers.SerializerMethodField()
    academic_year = serializers.CharField(source="academic_year.name", read_only=True)  # ? read-only
    
    class Meta:
        model = GradesReport
        fields = [
            'id', 'student', 'student_name',
            'grade_class', 'grade_class_name',
            'period_average', 'semester_1_avg', 'semester_2_avg',
            'yearly_average', 'rank', 'period_grades', 'remark',
            'academic_year'
        ]

    def create(self, validated_data):
        from academicyear.models import AcademicYear
        active_year = AcademicYear.objects.filter(is_active=True).first()
        if not active_year:
            raise serializers.ValidationError("No active academic year found.")
        validated_data["academic_year"] = active_year
        return super().create(validated_data)

    def get_rank(self, obj):
        return obj.get_yearly_rank()

    def get_period_grades(self, obj):
        distributions = GradeDistribution.objects.filter(student=obj.student)
        return [
            {
                'subject_name': distribution.subject.name,
                'period_name': distribution.period.name,
                'formatted_final_score': distribution.formatted_final_score()
            }
            for distribution in distributions
        ]

    def get_remark(self, obj):
        return obj.get_remark()

    def get_yearly_average(self, obj):
        return obj.yearly_average()
    
    def get_semester_1_avg(self, obj):
        return obj.semester_average(1)
    
    def get_semester_2_avg(self, obj):
        return obj.semester_average(2)
    
    def get_period_average(self, obj):
       
        period_names = set([distribution.period.name for distribution in GradeDistribution.objects.filter(student=obj.student)])
        averages = {}
        for period_name in period_names:
            period_avg = obj.period_average(period_name)  
            averages[period_name] = period_avg  
        return averages

