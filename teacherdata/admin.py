from django.contrib import admin
from teacherdata.models import SupportStaff, TeacherDataProcess, TeacherLessonPlan



@admin.register(TeacherDataProcess)
class TeacherSalaryAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'division',
        'get_subjects',
        'get_grade_classes',  # ✅ Add this
        'full_name',
        'qualification',
        'dependent_student',
        'salary',
        'date_add',
    )
    search_fields = ('username__email', 'full_name')

    def get_subjects(self, obj):
        return ", ".join(subject.name for subject in obj.subjects.all())
    get_subjects.short_description = 'Subjects'

    def get_grade_classes(self, obj):
        return ", ".join(gc.name for gc in obj.grade_class.all())
    get_grade_classes.short_description = 'Grade Classes'


@admin.register(SupportStaff)
class SupportStaffAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'salary', 'date_add')
    search_fields = ('full_name', 'department', 'contact')
    list_filter = ('department', 'date_add')



@admin.register(TeacherLessonPlan)
class TeacherLessonPlanAdmin(admin.ModelAdmin):
    list_display = ('period', 'teacher', 'subject', 'grade_class', 'week', 'date_created')
    search_fields = ('topic', 'objectives', 'teacher__full_name', 'subject__name')
    list_filter = ('subject', 'grade_class', 'week')