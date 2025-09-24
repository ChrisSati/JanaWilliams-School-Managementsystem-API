from rest_framework import serializers

from users.models import User
from .models import Payroll, SalaryAdvance
from teacherdata.models import  TeacherDataProcess

class TeacherMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherDataProcess
        fields = ['id', 'full_name']

class PayrollSerializer(serializers.ModelSerializer):
    teacher = TeacherMiniSerializer(read_only=True)
    
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=TeacherDataProcess.objects.all(),
        source='teacher',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Payroll
        fields = [
            'id', 'teacher', 'teacher_id',
            'support_staff_name', 'month', 'year', 'salary_advance',
            'basic_salary', 'bonus', 'deductions',
            'total_paid', 'is_paid', 'created_at'
        ]
        read_only_fields = ['total_paid', 'created_at']

    def validate(self, data):
        teacher = data.get('teacher')
        support_staff_name = data.get('support_staff_name')

        if not teacher and not support_staff_name:
            raise serializers.ValidationError("Either teacher or support staff name is required.")
        if teacher and support_staff_name:
            raise serializers.ValidationError("Only one of teacher or support staff name should be provided.")

        return data


class SalaryAdvanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    support_staff_name = serializers.CharField(source='support_staff.full_name', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = SalaryAdvance
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'support_staff',
            'support_staff_name',
            'amount',
            'created_at',
            'reason',
            'month',
            'year',
        ]


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'user_type']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['full_name'] = instance.get_full_name()
        return data





