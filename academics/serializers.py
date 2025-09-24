from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from django.db.models import Avg
# from users.models import User

from complaint.serializers import ComplaintSerializer
from users.models import User
from scoolfeedata.serializers import PaymentSerializer
from users.serializers import UserSerializer
from .models import  Division, StudentAdmission, Subject, GradeClass,  Assignment





class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = ['id', 'name', 'created_at', 'updated_at']

class GradeClassSerializer(serializers.ModelSerializer):
    division = DivisionSerializer(read_only=True)  # Show division details in GET
    division_id = serializers.PrimaryKeyRelatedField(
        queryset=Division.objects.all(),
        source='division',  # Assigns to the actual model field
        write_only=True     # Only used during POST/PUT
    )

    class Meta:
        model = GradeClass
        fields = ['id', 'name', 'division', 'division_id']



class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = ['id', 'name', 'created_at', 'updated_at']



class SubjectSerializer(serializers.ModelSerializer):
    division_assigned_name = GradeClassSerializer(source='division_assigned', read_only=True)
    class Meta:
        model = Subject
        fields = ['id', 'name', 'division_assigned', 'division_assigned_name']
        # fields = '__all__'



class StudentAdmissionSerializer(serializers.ModelSerializer):
    full_name_name = serializers.CharField(source='full_name', read_only=True)

    complaints = ComplaintSerializer(many=True, read_only=True)
    
    division_assigned_name = serializers.CharField(source='division_assigned.name', read_only=True)
    grade_class_name = serializers.CharField(source="grade_class.name", read_only=True)
    parent_name = serializers.CharField(source='parent.full_name', read_only=True, default=None)

    total_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    balance_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    total_present = serializers.IntegerField(read_only=True)
    total_absent = serializers.IntegerField(read_only=True)
    total_late = serializers.IntegerField(read_only=True)

    profile_image = serializers.SerializerMethodField()

    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent',
        queryset=User.objects.exclude(user_type='student'),
        required=False,
        allow_null=True
    )

    class Meta:
        model = StudentAdmission
        fields = '__all__'

    def get_profile_image(self, obj):
        image_field = getattr(obj.user, 'profile_image', None)
        if not image_field:
            return None
        if not getattr(image_field, 'url', None):
            return None

        request = self.context.get('request')
        url = image_field.url
        return request.build_absolute_uri(url) if request else url



class StudentAdmissionDetailSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)
    grade_class = serializers.CharField(source='grade_class.name', read_only=True)
    division = serializers.CharField(source='division_assigned.name', read_only=True)

    class Meta:
        model = StudentAdmission
        fields = [
            'id',
            'parent_name',
            'full_name',
            'grade_class',
            'major_subject',
            'hobit',
            'date_of_birth',
            'address',
            'mother_name',
            'father_name',
            'health_status',
            'parent_contact',
            'status',
            'nationality',
            'division'
        ]








class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'


# NEW: Subject Count by Division Serializer
class SubjectCountByDivisionSerializer(serializers.Serializer):
    division_name = serializers.CharField()
    subject_count = serializers.IntegerField()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

