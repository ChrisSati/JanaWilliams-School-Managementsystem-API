from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from teacherdata.models import TeacherDataProcess
from .models import StudentAttendance
from .serializers import StudentAttendanceSerializer



class CanTakeAttendance(permissions.BasePermission):
    """Only allow certain user types to take attendance."""
    def has_permission(self, request, view):
        return request.user.user_type in ["admin", "teacher", "registry", "vpi", "vpa", "dean"]


class StudentAttendanceViewSet(viewsets.ModelViewSet):
    """
    Handles single attendance record creation.
    """
    serializer_class = StudentAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, CanTakeAttendance]

    def get_queryset(self):
        queryset = self.get_filtered_queryset_by_role()
        grade_class_id = self.request.query_params.get("grade_class")
        if grade_class_id:
            queryset = queryset.filter(grade_class_id=grade_class_id)
        return queryset.select_related("student", "grade_class", "student__user").order_by("-date")

    def get_filtered_queryset_by_role(self):
        user = self.request.user
        if user.user_type in ["admin", "dean", "vpa", "vpi"]:
            return StudentAttendance.objects.all()
        elif user.user_type == "teacher":
            try:
                teacher = TeacherDataProcess.objects.get(username=user)
                assigned_classes = teacher.grade_class.all()
                return StudentAttendance.objects.filter(grade_class__in=assigned_classes)
            except TeacherDataProcess.DoesNotExist:
                return StudentAttendance.objects.none()
        return StudentAttendance.objects.none()

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_create(self, serializer):
        """
        Automatically set `taken_by` to the logged-in user.
        """
        serializer.save(taken_by=self.request.user)


class BulkCreateStudentAttendanceView(APIView):
    """
    Dedicated endpoint for bulk attendance creation.
    Creates new records or updates existing ones for the same student and date.
    """
    permission_classes = [permissions.IsAuthenticated, CanTakeAttendance]

    def post(self, request, *args, **kwargs):
        data = request.data
        if not isinstance(data, list):
            return Response(
                {"error": "Expected a list of attendance records."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = []
        for record in data:
            student_id = record.get("student")
            date = record.get("date")
            grade_class_id = record.get("grade_class")
            status_value = record.get("status")

            # Update existing record or create new
            obj, created = StudentAttendance.objects.update_or_create(
                student_id=student_id,
                date=date,
                defaults={
                    "grade_class_id": grade_class_id,
                    "status": status_value,
                    "taken_by": request.user,
                },
            )

            response_data.append({
                "student": student_id,
                "date": date,
                "created": created
            })

        return Response(
            {
                "message": "Attendance processed successfully",
                "details": response_data
            },
            status=status.HTTP_200_OK,
        )