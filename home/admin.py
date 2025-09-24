from django.contrib import admin
from .models import Slide, AdmissionAnnouncement, Card, Staff, HomePopup

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'description', 'image_preview')
    list_editable = ('order',)
    ordering = ('order',)
    search_fields = ('title', 'description')
    
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" />'
        return "-"
    image_preview.allow_tags = True
    image_preview.short_description = 'Preview'


@admin.register(AdmissionAnnouncement)
class AdmissionAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'highlight', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'highlight', 'description')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'image')

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'role', 'description', 'image')

@admin.register(HomePopup)
class HomePopupAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'image')