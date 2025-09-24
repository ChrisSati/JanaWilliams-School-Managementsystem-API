from django.urls import path
from users.views import student_admission_detail, subject_count_by_student_division


urlpatterns = [
    # other routes...
    path('subject-count-by-division/', subject_count_by_student_division, name='subject-count-by-division'),
    path("student-admission-detail/", student_admission_detail, name="student-admission-detail"),
]
