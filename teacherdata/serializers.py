from academics.models import GradeClass, Subject
from users.models import User
from teacherdata.models import SupportStaff, TeacherDataProcess, TeacherLessonPlan
from django.core.exceptions import ValidationError
from rest_framework import serializers

class TeacherDataProcessSerializer(serializers.ModelSerializer):
    division_name = serializers.CharField(source='division.name', read_only=True)

    username = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type__in=['teacher', 'admin', 'vpi', 'vpa', 'dean', 'it personel', 'business manager'])
    )

    subjects = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Subject.objects.all(),
        required=False  # <-- Make optional
    )

    grade_class = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=GradeClass.objects.all(),
        required=False  # <-- Make optional
    )

    class Meta:
        model = TeacherDataProcess
        fields = '__all__'


# class TeacherDataProcessSerializer(serializers.ModelSerializer):
#     division_name = serializers.CharField(source='division.name', read_only=True)

#     user = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.filter(user_type__in=[
#             'teacher', 'admin', 'vpi', 'vpa', 'dean', 'it personel', 'business manager'
#         ])
#     )

#     subjects = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=Subject.objects.all(),
#         required=False
#     )

#     grade_class = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=GradeClass.objects.all(),
#         required=False
#     )

#     class Meta:
#         model = TeacherDataProcess
#         fields = '__all__'





class TeacherInfoSerializer(serializers.ModelSerializer):
    grade_class = serializers.StringRelatedField(many=True)  # Optional: or use nested serializer
    division = serializers.StringRelatedField()

    class Meta:
        model = TeacherDataProcess
        fields = ['qualification', 'division', 'grade_class', 'dependent_student', 'salary']



class TeacherLessonPlanSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    period_name = serializers.CharField(source='period.name', read_only=True)

    class Meta:
        model = TeacherLessonPlan
        fields = '__all__'
        read_only_fields = ['teacher']  # Prevent "teacher required" errors

    def validate(self, data):
        teacher = self.context['request'].user
        subject = data.get('subject')
        grade_class = data.get('grade_class')

        # Only run this validation for teachers linked to TeacherDataProcess
        if teacher.user_type == 'teacher':
            teacher_data = getattr(teacher, 'teacherdataprocess', None)
            if not teacher_data:
                raise serializers.ValidationError("TeacherDataProcess not found for the teacher.")

            if subject not in teacher_data.subjects.all():
                raise serializers.ValidationError("This subject is not assigned to the teacher.")

            if grade_class not in teacher_data.grade_class.all():
                raise serializers.ValidationError("This grade class is not assigned to the teacher.")

        # Skip validation for admin, vpi, vpa
        return data

# class TeacherLessonPlanSerializer(serializers.ModelSerializer):
#     subject_name = serializers.CharField(source='subject.name', read_only=True)
#     grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)
#     teacher_name = serializers.CharField(source='teacher.username', read_only=True)
#     period_name = serializers.CharField(source='period.name', read_only=True)

#     class Meta:
#         model = TeacherLessonPlan
#         fields = '__all__'
#         read_only_fields = ['teacher']  # ✅ This prevents "teacher required" errors

#     def validate(self, data):
#         teacher = self.context['request'].user
#         subject = data.get('subject')
#         grade_class = data.get('grade_class')

#         # Ensure the subject and grade_class are assigned to the teacher
#         teacher_data = teacher.teacherdataprocess

#         if subject not in teacher_data.subjects.all():
#             raise serializers.ValidationError("This subject is not assigned to the teacher.")

#         if grade_class not in teacher_data.grade_class.all():
#             raise serializers.ValidationError("This grade class is not assigned to the teacher.")

#         return data


# class SupportStaffSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SupportStaff
#         fields = '__all__'

#     def validate_image(self, value):
#         if value:
#             valid_extensions = ['jpg', 'jpeg', 'png']
#             ext = value.name.split('.')[-1].lower()
#             if ext not in valid_extensions:
#                 raise ValidationError("Unsupported file extension. Allowed: jpg, jpeg, png.")
#         return value


class SupportStaffSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)  # This tells DRF to return a URL, not a file path

    class Meta:
        model = SupportStaff
        fields = '__all__'

    def validate_image(self, value):
        if value:
            valid_extensions = ['jpg', 'jpeg', 'png']
            ext = value.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError("Unsupported file extension. Allowed: jpg, jpeg, png.")
        return value




class TeacherSubjectsSerializer(serializers.ModelSerializer):
    subjects = serializers.SerializerMethodField()
    grade_classes = serializers.SerializerMethodField()
    teacher_id = serializers.IntegerField(source='id')

    class Meta:
        model = TeacherDataProcess
        fields = ['teacher_id', 'subjects', 'grade_classes']

    def get_subjects(self, obj):
        return [{"id": s.id, "name": s.name} for s in obj.subjects.all()]

    def get_grade_classes(self, obj):
        return [{"id": gc.id, "name": gc.name} for gc in obj.grade_class.all()]

