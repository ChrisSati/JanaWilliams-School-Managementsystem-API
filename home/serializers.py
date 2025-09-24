from rest_framework import serializers
from .models import Slide, AdmissionAnnouncement, Card, Staff, HomePopup

class SlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slide
        fields = ['id', 'title', 'description', 'image', 'order']




class AdmissionAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionAnnouncement
        fields = ['id', 'title', 'highlight', 'description', 'button_text', 'image', 'is_active']


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'title', 'description', 'image']

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'

class HomePopupSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomePopup
        fields = '__all__'