from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    ExpenditureViewSet,
    FeesPerGradeClassViewSet,
    FeeViewSet,
    MonthlyFinancialRecordViewSet,
    FinancialLineItemViewSet,
    YearlyFinancialReportView
)

router = DefaultRouter()
router.register(r'expenditures', ExpenditureViewSet)
router.register(r'fees-per-grade-class', FeesPerGradeClassViewSet)
router.register(r'special-fees', FeeViewSet)
router.register(r'financial-records', MonthlyFinancialRecordViewSet) 
router.register(r'line-items', FinancialLineItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('yearly-report/', YearlyFinancialReportView.as_view(), name='yearly-financial-report'),
]
