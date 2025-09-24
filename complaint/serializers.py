from rest_framework import serializers
from .models import Complaint

class ComplaintSerializer(serializers.ModelSerializer):
    # Read-only convenience fields for UI
    poster_username = serializers.CharField(source='poster.username', read_only=True)
    student_full_name = serializers.CharField(source='student.full_name', read_only=True)
    poster_name = serializers.CharField(source='poster.username', read_only=True)
    poster_user_type = serializers.CharField(source='poster.user_type', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id',
            'poster',          # read-only; set from request.user
            'poster_name',
            'poster_username',
            'poster_user_type',
            'student',
            'student_full_name',
            'title',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['poster', 'created_at', 'updated_at']
