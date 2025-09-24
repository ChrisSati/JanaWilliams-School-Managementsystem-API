from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os
from rest_framework.routers import DefaultRouter


from .views import SalaryAdvanceViewSet, current_month_salary_advance, get_teacher_salary
from .views import PayrollViewSet

router = DefaultRouter()
router.register(r'payrolls', PayrollViewSet, basename='payroll')
router.register(r'salary-advances', SalaryAdvanceViewSet, basename='salary-advance')



urlpatterns = [
    path('', include(router.urls)),
    path('teacher-salary/<int:teacher_id>/', get_teacher_salary, name='get-teacher-salary'),
    path('current-month-salary-advance/', current_month_salary_advance, name='current_month_salary_advance'),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, "payroll/static"))


