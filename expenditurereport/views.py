from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import (
    Expenditure,
    FeesPerGradeClass,
    Fee,
    MonthlyFinancialRecord,
    FinancialLineItem
)
from .serializers import (
    ExpenditureSerializer,
    FeesPerGradeClassSerializer,
    FeeSerializer,
    MonthlyFinancialRecordSerializer,
    FinancialLineItemSerializer
)
from rest_framework.decorators import action
from django.db.models import Sum


class ExpenditureViewSet(viewsets.ModelViewSet):
    queryset = Expenditure.objects.all().order_by('-date')
    serializer_class = ExpenditureSerializer

    @action(detail=False, methods=['get'])
    def total_amount(self, request):
        total = Expenditure.objects.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        return Response({'total_amount': total})




class FeesPerGradeClassViewSet(viewsets.ModelViewSet):
    queryset = FeesPerGradeClass.objects.all().order_by('-year', 'semester')
    serializer_class = FeesPerGradeClassSerializer


class FeeViewSet(viewsets.ModelViewSet):
    queryset = Fee.objects.all().order_by('-date_paid')
    serializer_class = FeeSerializer


class MonthlyFinancialRecordViewSet(viewsets.ModelViewSet):
    queryset = MonthlyFinancialRecord.objects.all().order_by('-created_at')
    serializer_class = MonthlyFinancialRecordSerializer



class YearlyFinancialReportView(APIView):
    permission_classes = [IsAuthenticated]  # <--- Require authentication

    def get(self, request):
        records = MonthlyFinancialRecord.objects.all().order_by('year')

        yearly_summary = {}

        for record in records:
            year = record.year
            if year not in yearly_summary:
                yearly_summary[year] = {
                    'year': year,
                    'donation_income': 0,
                    'school_fees_total': 0,
                    'staff_salary_total': 0,
                    'staff_loan_total': 0,
                    'salary_advance_total': 0,
                    'other_expenditures_total': 0,
                    'total_income': 0,
                    'total_expenses': 0,
                    'net_balance': 0,
                }

            yearly_summary[year]['donation_income'] += float(record.donation_income)
            yearly_summary[year]['school_fees_total'] += float(record.school_fees_total)
            yearly_summary[year]['staff_salary_total'] += float(record.staff_salary_total)
            yearly_summary[year]['staff_loan_total'] += float(record.staff_loan_total)
            yearly_summary[year]['salary_advance_total'] += float(record.salary_advance_total)
            yearly_summary[year]['other_expenditures_total'] += float(record.other_expenditures_total)
            yearly_summary[year]['total_income'] += float(record.total_income)
            yearly_summary[year]['total_expenses'] += float(record.total_expenses)
            yearly_summary[year]['net_balance'] += float(record.net_balance)

        result = list(yearly_summary.values())
        return Response(result)


class FinancialLineItemViewSet(viewsets.ModelViewSet):
    queryset = FinancialLineItem.objects.all()
    serializer_class = FinancialLineItemSerializer
