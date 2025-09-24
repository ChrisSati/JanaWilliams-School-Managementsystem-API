from teachersalary.models import StaffSalary
from rest_framework import serializers

class StaffSalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffSalary
        fields = '__all__'

