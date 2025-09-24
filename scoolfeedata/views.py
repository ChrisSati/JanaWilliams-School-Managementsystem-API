from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from receiptrecord.models import SchoolFeePayment
from .serializers import SchoolFeePaymentSerializer
from rest_framework import viewsets, status
from scoolfeedata.serializers import SchoolFeePaymentSerializer



class SchoolFeePaymentListCreateView(viewsets.ModelViewSet):
    queryset = SchoolFeePayment.objects.all()
    serializer_class = SchoolFeePaymentSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        receipt_number = kwargs.get("pk")
        try:
            receipt = SchoolFeePayment.objects.get(receipt_number=receipt_number)
        except SchoolFeePayment.DoesNotExist:
            return Response({"error": "Receipt not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(receipt, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




