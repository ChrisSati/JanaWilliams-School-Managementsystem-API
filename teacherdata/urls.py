from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupportStaffViewSet, TeacherLessonPlanViewSet, TeacherSubjectsAPIView

router = DefaultRouter()
router.register(r'supportstaff', SupportStaffViewSet, basename='supportstaff')
router.register('lesson-plans', TeacherLessonPlanViewSet, basename='lesson-plan')

urlpatterns = [
    path('', include(router.urls)),
    path('api/users/teacher-subjects/', TeacherSubjectsAPIView.as_view(), name='teacher-subjects'),
]
