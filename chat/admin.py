from django.contrib import admin
from django.utils.html import format_html
from chat.models import Chat

@admin.register(Chat)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sender_name',
        'receiver_name',
        'message',
        'timestamp',
        'sender_profile_image',
        'receiver_profile_image',
    )

    search_fields = ('sender__username', 'receiver__username', 'message')
    list_filter = ('timestamp',)

    def sender_name(self, obj):
        return obj.sender.username if obj.sender else 'Unknown'
    sender_name.admin_order_field = 'sender__username'
    sender_name.short_description = 'Sender'

    def receiver_name(self, obj):
        return obj.receiver.username if obj.receiver else 'Unknown'
    receiver_name.admin_order_field = 'receiver__username'
    receiver_name.short_description = 'Receiver'

    def sender_profile_image(self, obj):
        if obj.sender and obj.sender.profile_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.sender.profile_image.url
            )
        return 'No Image'
    sender_profile_image.short_description = 'Sender Image'

    def receiver_profile_image(self, obj):
        if obj.receiver and obj.receiver.profile_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.receiver.profile_image.url
            )
        return 'No Image'
    receiver_profile_image.short_description = 'Receiver Image'
