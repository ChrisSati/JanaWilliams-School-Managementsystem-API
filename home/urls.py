from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SlideViewSet, AdmissionAnnouncementViewSet, CardViewSet, StaffViewSet, HomePopupViewSet

router = DefaultRouter()
router.register(r'slides', SlideViewSet, basename='slides')
router.register(r'announcements', AdmissionAnnouncementViewSet, basename='announcements')
router.register(r'cards', CardViewSet, basename='card')
router.register(r'staff', StaffViewSet)
router.register(r'home-popups', HomePopupViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
