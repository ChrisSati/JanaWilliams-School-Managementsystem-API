from rest_framework import serializers
from academics.serializers import GradeClassSerializer, SubjectSerializer
from academics.models import GradeClass, Subject
from teacherdata.models import TeacherDataProcess
from teacherdata.serializers import TeacherDataProcessSerializer
from .models import ClassSchedule


class ClassScheduleSerializer(serializers.ModelSerializer):
    grade_class = GradeClassSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    teacher = TeacherDataProcessSerializer(read_only=True)

    profile_image = serializers.SerializerMethodField()

    grade_class_id = serializers.PrimaryKeyRelatedField(
        queryset=GradeClass.objects.all(), source="grade_class", write_only=True
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject", write_only=True
    )
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=TeacherDataProcess.objects.all(), source="teacher", write_only=True
    )

    duration_minutes = serializers.SerializerMethodField()
    day_label = serializers.SerializerMethodField()
    period_label = serializers.SerializerMethodField()

    class Meta:
        model = ClassSchedule
        fields = [
            "id",
            "grade_class", "grade_class_id",
            "subject", "subject_id",
            "teacher", "teacher_id",
            "profile_image",  # ✅ Exposed here for frontend
            "day_of_week", "day_label",
            "period", "period_label",
            "start_time", "end_time",
            "duration_minutes",
        ]

    def get_duration_minutes(self, obj):
        return obj.duration_minutes

    def get_profile_image(self, obj):
        request = self.context.get("request")
        user = getattr(obj.teacher, "username", None)  # ✅ username = FK to User
        if request and user and user.profile_image:
            return request.build_absolute_uri(user.profile_image.url)
        return None

    def get_day_label(self, obj):
        return obj.get_day_of_week_display()

    def get_period_label(self, obj):
        return obj.get_period_display()

