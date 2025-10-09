from django.contrib import admin
from .models import StudentAttendance, Announcement, BackgroundImage

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'grade_class', 'date', 'status', 'taken_by']
    list_filter = ['grade_class', 'date', 'status']
    search_fields = ['student__full_name', 'taken_by__full_name']






@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'subtitle', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('title', 'subtitle', 'content', 'created_by__full_name')
    ordering = ('-created_at',)

@admin.register(BackgroundImage)
class BackgroundImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'updated_at')
    ordering = ('-updated_at',)

