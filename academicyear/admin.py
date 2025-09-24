from django.contrib import admin
from .models import AcademicYear

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    ordering = ("-start_date",)
    search_fields = ("name",)