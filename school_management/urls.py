from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.conf.urls.static import static
from rest_framework_simplejwt.views import  TokenRefreshView
from reportcard.views import FilterStudentsByGradeClassView
from users.views import CustomLogoutView, CustomTokenObtainPairView, CustomTokenRefreshView, GradeClassCountView, GradeClassRetrieveUpdateDestroyView, MyLinkedStudentsView, PaymentViewSet, RegistrationView, StaffSalaryView, StudentAdmissionCountView, StudentRetrieveUpdateDeleteView, StudentUserListView, SubjectCountView, SubjectRetrieveUpdateDestroyView, SuperParentsListView, TeacherUserListView,  UserLoginView, UserProfileView, UserViewSet, count_by_gender, count_by_semester, get_students



urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/', include('home.urls')),
    path('', include('classschedule.urls')),
    path('', include('resetpasscode.urls')), 
    # path('', include('chatnotification.urls')),
    # path('', include('chat.urls')),
    path('', include('complaint.urls')),
    path('', include('attendance.urls')),
    path('', include('academics.urls')),
    path('', include('reportcard.urls')),
    path('', include('payroll.urls')),
    path('', include('teacherdata.urls')),
    path('', include('teacherdata.urls')),
    path('', include('expenditurereport.urls')),
    path('', include('loan.urls')), 
    path('', include('onlinetestlivetest.urls')), 
    path('', include('academicyear.urls')),
    path('students/filter/', get_students, name='student-filter'),
    path("students-by-grade-class/", FilterStudentsByGradeClassView.as_view(), name="students-by-grade-class"),
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('user-profile/', UserProfileView.as_view(), name='user-profile'),
   
    path('staff-salaries/', StaffSalaryView.as_view(), name='staff-salaries'),
    
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', CustomLogoutView.as_view(), name='logout'),
    

    path('api/user-profile/', UserProfileView.as_view(), name='user-profile'),
    path('api/admission_count/', StudentAdmissionCountView.as_view(), name='admission-count'),
    path('users/', UserViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-list'),
    path('api/students/count-by-semester/', count_by_semester, name='count-by-semester'),
    path('api/students/count-by-gender/', count_by_gender, name='count-by-gender'),
  
    path('grade-classes/count/', GradeClassCountView.as_view(), name='gradeclass-count'),
    path('subjects/count/', SubjectCountView.as_view(), name='subject-count'),
    
    path('api/students/', StudentUserListView.as_view(), name='student-users'),
    path('api/super-parents/', SuperParentsListView.as_view(), name='super-parent-list'),
    path('admissions/my-linked-students/', MyLinkedStudentsView.as_view(), name='my-linked-students'),

    path('api/teacherslist/', TeacherUserListView.as_view(), name='student-users'),

 

    path('grade-classes-retrive/<int:pk>/', GradeClassRetrieveUpdateDestroyView.as_view(), name='gradeclass-detail'),
    path('subjects-retrive/<int:pk>/', SubjectRetrieveUpdateDestroyView.as_view(), name='subject-detail'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
