from django.urls import path
from .views import AcademicYearListView, ActiveAcademicYearView

urlpatterns = [
    path('academic-years/', AcademicYearListView.as_view(), name='academic-years'),
    path('academic-years/active/', ActiveAcademicYearView.as_view(), name='active-academic-year'),
]