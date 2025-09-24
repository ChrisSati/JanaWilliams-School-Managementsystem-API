from rest_framework import serializers
from academics.models import StudentAdmission
from receiptrecord.models import SchoolFeePayment
from scoolfeedata.models import Payment, SchoolFeesData



class SchoolFeesDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolFeesData
        fields = '__all__'




class PaymentSerializer(serializers.ModelSerializer):
    student_class_name = serializers.CharField(source="student_class.name", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
  

    class Meta:
        model = Payment
        fields = '__all__'


class SchoolFeePaymentSerializer(serializers.ModelSerializer):
    grade_class = serializers.CharField(source='student.grade_class.name', read_only=True)
    student_full_name = serializers.CharField(source='student.full_name', read_only=True)
    balance = serializers.ReadOnlyField()

    class Meta:
        model = SchoolFeePayment
        fields = ['id', 'receipt_number', 'student', 'student_class', 'payer_name',  'payer_contact', 'grade_class', 'student_full_name', 'receipt_number', 'semester', 'services', 'amount_due', 'amount_paid', 'balance', 'date']
        read_only_fields = ['balance', 'grade_class', 'student_full_name']








