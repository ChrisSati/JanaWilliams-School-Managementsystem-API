from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BulkCreateStudentAttendanceView, StudentAttendanceViewSet

router = DefaultRouter()
router.register(r'student-attendance', StudentAttendanceViewSet, basename='student-attendance')

urlpatterns = [
    # Custom bulk-create route must be before router includes:
    path('student-attendance/bulk-create/', BulkCreateStudentAttendanceView.as_view(), name='bulk-create'),
    path('', include(router.urls)),
]





# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import BulkCreateStudentAttendanceView, StudentAttendanceViewSet, StudentListView

# router = DefaultRouter()
# router.register(r'student-attendance', StudentAttendanceViewSet, basename='student-attendance')

# urlpatterns = [
#     path('student-attendance/bulk-create/', BulkCreateStudentAttendanceView.as_view(), name='bulk-create'),
#     path('', include(router.urls)),
# ]
