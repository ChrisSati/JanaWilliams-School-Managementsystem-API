from rest_framework import serializers

from academics.serializers import GradeClassSerializer
from academics.models import GradeClass
from .models import (
    Expenditure,
    FeesPerGradeClass,
    Fee,
    MonthlyFinancialRecord,
    FinancialLineItem
)


class ExpenditureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenditure
        fields = '__all__'
        

class FeesPerGradeClassSerializer(serializers.ModelSerializer):
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)
    fees_expected = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    fees_collected = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = FeesPerGradeClass
        fields = [
            'id', 'grade_class', 'grade_class_name', 'semester', 'year',
            'fees_expected', 'fees_collected', 'balance'
        ]



# class FeeSerializer(serializers.ModelSerializer):
#     student_name = serializers.CharField(source='student.full_name', read_only=True)
#     grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)

#     class Meta:
#         model = Fee
#         fields = '__all__'


class FeeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)

    class Meta:
        model = Fee
        fields = '__all__'

    def validate(self, data):
        fee_type = data.get("fee_type")
        student = data.get("student")
        entrance_name = data.get("entrance_student_name")

        # 🔒 Only one should be used depending on fee_type
        if fee_type == "entrance":
            if not entrance_name:
                raise serializers.ValidationError({"entrance_student_name": "This field is required for Entrance Fee."})
        else:
            if not student:
                raise serializers.ValidationError({"student": "This field is required for non-Entrance Fee types."})
            if entrance_name:
                raise serializers.ValidationError({"entrance_student_name": "Should not be provided for non-Entrance Fee types."})

        return data


# class FeeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Fee
#         fields = '__all__'


class MonthlyFinancialRecordSerializer(serializers.ModelSerializer):
    school_fees_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    salary_advance_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    staff_loan_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    staff_salary_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    other_expenditures_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    net_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = MonthlyFinancialRecord
        fields = '__all__'


class FinancialLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialLineItem
        fields = '__all__'
