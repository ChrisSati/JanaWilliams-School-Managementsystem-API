from django.contrib import admin

from academics.models import GradeClass, Subject
from teacherdata.models import TeacherDataProcess
from .models import  ClassSchedule


# @admin.register(GradeClass)
# class GradeClassAdmin(admin.ModelAdmin):
#     list_display  = ("name",)
#     search_fields = ("name",)


# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display  = ("name", "code")
#     search_fields = ("name", "code")


# @admin.register(TeacherDataProcess)
# class TeacherAdmin(admin.ModelAdmin):
#     list_display  = ("full_name", "email", "contact")
#     search_fields = ("full_name", "email")
#     list_filter   = ("full_name",)


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display  = ("period",
        "grade_class", "subject", "teacher",
        "day_of_week", "start_time", "end_time", "duration_minutes",
    )
    list_filter   = ("grade_class", "day_of_week", "teacher")
    search_fields = ("subject__name", "teacher__full_name")
    ordering      = ("day_of_week", "start_time")

    # Nice derived column
    def duration_minutes(self, obj):
        return obj.duration
    duration_minutes.short_description = "Duration (min)"
