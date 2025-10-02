from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentAttendanceViewSet, BulkCreateStudentAttendanceView

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
]


