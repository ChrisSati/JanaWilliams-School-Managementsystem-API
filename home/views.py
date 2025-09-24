from rest_framework import viewsets, permissions
from .models import Slide, AdmissionAnnouncement, Card, Staff, HomePopup
from .serializers import SlideSerializer, AdmissionAnnouncementSerializer, CardSerializer, StaffSerializer, HomePopupSerializer

class SlideViewSet(viewsets.ModelViewSet):
    queryset = Slide.objects.all()
    serializer_class = SlideSerializer
    permission_classes = [permissions.AllowAny] 



class AdmissionAnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdmissionAnnouncement.objects.filter(is_active=True)
    serializer_class = AdmissionAnnouncementSerializer
    permission_classes = [permissions.AllowAny]


class CardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [permissions.AllowAny]

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

class HomePopupViewSet(viewsets.ModelViewSet):
    queryset = HomePopup.objects.all()
    serializer_class = HomePopupSerializer