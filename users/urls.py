from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reportcard.views import GradeDistributionListView, GradesReportViewSet, PeriodViewSet, StudentAverageViewSet
from notifications.views import NotificationViewSet
from chat.views import ChatViewSet, UserListAPIView
from chatnotification.views import ChatnotificationViewSet
from scoolfeedata.views import SchoolFeePaymentListCreateView
from .views import AllUsersViewSet, CountsView, DivisionViewSet, AdminResetPasswordView, ExpenditureViewSet, GradeClassViewSet, LinkedStudentGradesView, LoanViewSet, GradeClassListView, MyChildrenView, PaymentViewSet, StudentAdmissionView, SchoolFeesDataViewSet,  TeacherDataViewSet, UpdateProfileImageView, UserDetailsPageView, UserViewSet, SubjectViewSet, AssignmentViewSet


router = DefaultRouter()

# // chats

router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'chat-notifications', ChatnotificationViewSet, basename='chatnotification')

router.register(r'users', UserViewSet)
router.register(r'users-users', AllUsersViewSet, basename='user-user')
router.register(r'payments', PaymentViewSet, basename='payment')

router.register(r'periods', PeriodViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')  # Add basename here


# router.register(r'students-reportcards', GradesReportViewSet)
router.register(r'grades-reports', GradesReportViewSet, basename='grades-report')
router.register(r'student-averages', StudentAverageViewSet, basename='student-averages')
# router.register(r'student-averages', StudentAverageViewSet)
router.register(r'grades-distribution', GradeDistributionListView)
router.register(r'grade-classes', GradeClassListView)
router.register(r'grade-classes-view', GradeClassViewSet, basename='grade-class')
router.register(r'divisions', DivisionViewSet, basename='division')
router.register(r'students', StudentAdmissionView, basename='admissions')
router.register(r'assignments', AssignmentViewSet)
router.register(r'school-fees-data', SchoolFeesDataViewSet)
router.register(r'expenditures', ExpenditureViewSet)
router.register(r'teacher-data', TeacherDataViewSet)
router.register(r'loans', LoanViewSet)
router.register(r'students-reciept', SchoolFeePaymentListCreateView)






urlpatterns = [
    path('', include(router.urls)),
    path('my-children/', MyChildrenView.as_view(), name='my-children'),
    path("user-page-details/", UserDetailsPageView.as_view(), name="user-details-page"),
    path('chat/userslist/', UserListAPIView.as_view(), name='user-list'),
    path('admin-counts/', CountsView.as_view(), name='admin-counts'),
    path('linked-student-grades/', LinkedStudentGradesView.as_view(), name='linked-student-grades'),
    path('user/profileimage/', UpdateProfileImageView.as_view(), name='update-profile-image'),
    path("admin-reset-password/", AdminResetPasswordView.as_view(), name="admin-reset-password"),
]
