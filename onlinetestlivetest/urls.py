from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssignmentCommentDetail, AssignmentViewSet, OnlineTestViewSet, PeriodicTestViewSet, QuestionViewSet, StudentAnswerViewSet, TeacherDashboardView, get_test_and_students

router = DefaultRouter()
router.register(r'assignments', AssignmentViewSet)
router.register(r'online-tests', OnlineTestViewSet)
# router.register(r'test-questions', TestQuestionViewSet)
router.register(r'test-questions', QuestionViewSet, basename='question')

router.register('periodic-tests', PeriodicTestViewSet, basename='periodic-tests')
router.register('student-answers', StudentAnswerViewSet, basename='student-answers')

urlpatterns = [
    path('', include(router.urls)),
    path('teacher-dashboard/', TeacherDashboardView.as_view(), name='teacher-dashboard'),
    path('assignment-comments/<int:pk>/', AssignmentCommentDetail.as_view(), name='assignment-comment-detail'),
    path('api/test-with-students/', get_test_and_students, name='test-with-students'),
]
