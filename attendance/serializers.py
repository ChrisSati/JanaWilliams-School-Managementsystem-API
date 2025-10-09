from rest_framework import serializers
from .models import StudentAttendance, Announcement, BackgroundImage


class StudentAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    taken_by_name = serializers.CharField(source="taken_by.full_name", read_only=True)
    student_profile_image = serializers.SerializerMethodField()

    class Meta:
        model = StudentAttendance
        fields = [
            "id",
            "student",
            "student_name",
            "student_profile_image",
            "grade_class",
            "date",
            "status",
            "taken_by",
            "taken_by_name",
        ]
        read_only_fields = ["taken_by", "student_name", "taken_by_name"]

    def get_student_profile_image(self, obj):
        request = self.context.get("request")
        user = getattr(obj.student, "user", None)
        if user and getattr(user, "profile_image", None):
            return request.build_absolute_uri(user.profile_image.url)
        return None  # frontend can fallback to a default avatar

    def validate(self, attrs):
        request = self.context.get("request")
        if request is None:
            raise serializers.ValidationError("Request context is required.")

        user = request.user
        if user.user_type not in ["admin", "teacher", "registry", "vpi", "vpa", "dean"]:
            raise serializers.ValidationError("You are not allowed to take attendance.")

        return attrs






class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    role = serializers.CharField(source='created_by.role', read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'subtitle', 'content',
            'created_by', 'created_by_name', 'role',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class BackgroundImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackgroundImage
        fields = ['id', 'image', 'updated_at']