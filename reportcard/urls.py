from django.urls import path
from .views import AssignedGradeClassesView, AssignedSubjectsView, StudentsInGradeClassView, AcademicReportAllView, AcademicReportView, student_grade_performance

urlpatterns = [
    
    path('api/student-grade-performance/', student_grade_performance, name='student-grade-performance'),
    path('assigned-grade-classes/', AssignedGradeClassesView.as_view(), name='assigned-grade-classes'),
    path('assigned-subjects/', AssignedSubjectsView.as_view(), name='assigned-subjects'),
    path('students-in-class/<int:grade_class_id>/', StudentsInGradeClassView.as_view(), name='students-in-class'),
    path("academic-report/all/<int:period_id>/", AcademicReportAllView.as_view(), name="academic-report-all"),
    path(
        'academic-report/<int:grade_class_id>/<int:period_id>/',
        AcademicReportView.as_view(),
        name='academic-report'
    ),

]
