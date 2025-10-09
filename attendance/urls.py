from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentAttendanceViewSet, BulkCreateStudentAttendanceView, AnnouncementListCreateView, AnnouncementDetailView, BackgroundImageView

router = DefaultRouter()
router.register("student-attendance", StudentAttendanceViewSet, basename="student-attendance")

urlpatterns = [
    # Bulk endpoint MUST come first
    path(
        "student-attendance/bulk-create/",
        BulkCreateStudentAttendanceView.as_view(),
        name="bulk-create-attendance"
    ),
    path("", include(router.urls)),
    path('announcements/', AnnouncementListCreateView.as_view(), name='announcement-list'),
    path('announcements/<int:pk>/', AnnouncementDetailView.as_view(), name='announcement-detail'),
    path('background/', BackgroundImageView.as_view(), name='announcement-background'),
]


