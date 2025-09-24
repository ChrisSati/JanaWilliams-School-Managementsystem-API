# notifications/admin.py

from django.contrib import admin
from .models import Chatnotification

@admin.register(Chatnotification)
class ChatnotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'receiver', 'sender', 'message_preview', 'timestamp', 'is_read')
    search_fields = ('receiver__full_name', 'sender__full_name', 'message_preview')
    list_filter = ('is_read', 'timestamp')
