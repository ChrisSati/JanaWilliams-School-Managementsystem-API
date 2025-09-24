from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg
from academics.models import Division, GradeClass, StudentAdmission,  Subject, Assignment



@admin.register(GradeClass)
class GradeClassAdmin(admin.ModelAdmin):
    list_display = ("id",  "name",  "division")
    search_fields = ("name",)


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(StudentAdmission)
class StudentAdmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", 'parent_display', 'parent', "full_name", "gender", 'division_assigned', "county_of_origin", "previous_class",  "grade_class",
            "major_subject", "previous_school", "hobit", "date_of_birth", "address", "mother_name",  "father_name",
            "health_status", "parent_contact", "enrollment_date", 'gender', "semester_status", "status", "nationality",)
    search_fields = ('student__username', 'grade_class', 'full_name',  'county_of_origin', 'major_subject')
    list_filter = ('previous_class', 'grade_class', 'division_assigned', 'semester_status', 'enrollment_date',)

    def parent_display(self, obj):
        return obj.parent.get_full_name() if obj.parent else "-"
    parent_display.short_description = 'Parent'




@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',  'division_assigned')
    search_fields = ('name', 'division_assigned__name')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'assignment_subject', 'due_date', 'created_by')
    search_fields = ('title', 'assignment_subject__name', 'created_by__username')






