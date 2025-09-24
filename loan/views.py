from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import Loan
from .serializers import LoanSerializer

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all().order_by('-date_taken')
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='total-loan-amount')
    def total_loan_amount(self, request):
        total = Loan.objects.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        return Response({"total_loan_amount": total})
