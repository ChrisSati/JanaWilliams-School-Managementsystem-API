from django.contrib import admin
from .models import Complaint

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'student', 'poster', 'created_at')
    list_filter = ('poster__user_type', 'created_at')
    search_fields = ('title', 'description', 'student__full_name', 'poster__username')
    autocomplete_fields = ('student', 'poster')
