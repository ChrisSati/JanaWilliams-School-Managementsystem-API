from expenditure.models import Expenditure
from rest_framework import serializers

class ExpenditureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenditure
        fields = '__all__'