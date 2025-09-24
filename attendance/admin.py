from django.contrib import admin
from .models import StudentAttendance

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'grade_class', 'date', 'status', 'taken_by']
    list_filter = ['grade_class', 'date', 'status']
    search_fields = ['student__full_name', 'taken_by__full_name']


