from django.contrib import admin
from .models import Notification



class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'title', 'is_read', 'created_at']  # Fields to display in the admin list view
    list_filter = ['is_read', 'created_at']  # Filters to display on the right-hand side in the admin view
    search_fields = ['message', 'user__username']  # Add search functionality for message and user (username)
    ordering = ['-created_at']  # Order by creation date in descending order

    # Optionally, you can add actions to mark notifications as read from the admin
    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        # Custom action to mark selected notifications as read
        queryset.update(is_read=True)
        self.message_user(request, "Selected notifications have been marked as read.")
    
    mark_as_read.short_description = "Mark selected notifications as read"

# Register the model and its admin view
admin.site.register(Notification, NotificationAdmin)

# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ('user', 'message', 'created_at', 'is_read')
#     list_filter = ('is_read', 'created_at')
#     search_fields = ('user__username', 'message')
#     ordering = ('-created_at',)

# admin.site.register(Notification, NotificationAdmin)
