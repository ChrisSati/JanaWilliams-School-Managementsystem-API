from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from teacherdata.models import TeacherDataProcess
from .models import StudentAttendance
from .serializers import StudentAttendanceSerializer

class CanTakeAttendance(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type in ['admin', 'teacher', 'registry', 'vpi', 'vpa', 'dean']
    

class StudentAttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = StudentAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, CanTakeAttendance]

    def get_queryset(self):
        """
        Filter attendance records by:
        - Full access for 'admin', 'dean', 'vpa', 'vpi'
        - Assigned grade_class for teachers
        - Optional grade_class query param
        """
        queryset = self.get_filtered_queryset_by_role()
        grade_class_id = self.request.query_params.get("grade_class")

        if grade_class_id:
            queryset = queryset.filter(grade_class_id=grade_class_id)

        return queryset.select_related("student", "grade_class", "student__user").order_by("-date")

    def get_filtered_queryset_by_role(self):
        user = self.request.user
        user_type = getattr(user, "user_type", None)

        if user_type in ['admin', 'dean', 'vpa', 'vpi']: 
            return StudentAttendance.objects.all()

        elif user_type == 'teacher':
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
        serializer.save(taken_by=self.request.user)


# class StudentAttendanceViewSet(viewsets.ModelViewSet): 
#     serializer_class = StudentAttendanceSerializer
#     permission_classes = [permissions.IsAuthenticated, CanTakeAttendance]

#     def get_queryset(self):
#         queryset = (
#             StudentAttendance.objects
#             .select_related("student", "grade_class", "student__user")
#             .order_by("-date")
#         )
#         grade_class_id = self.request.query_params.get("grade_class")
#         if grade_class_id:
#             queryset = queryset.filter(grade_class_id=grade_class_id)
#         return queryset

#     def get_filtered_queryset_by_role(self):
#         """
#         Returns attendance queryset filtered by user role:
#         - admin, dean, vpa, vpi: full access
#         - teacher: only assigned grade classes
#         """
#         user = self.request.user
#         user_type = getattr(user, "user_type", None)

#         if user_type in ['admin', 'dean', 'vpa', 'vpi']:
#             return StudentAttendance.objects.all()

#         elif user_type == 'teacher':
#             try:
#                 teacher = TeacherDataProcess.objects.get(username=user)
#                 assigned_classes = teacher.grade_class.all()
#                 return StudentAttendance.objects.filter(grade_class__in=assigned_classes)
#             except TeacherDataProcess.DoesNotExist:
#                 return StudentAttendance.objects.none()

#         return StudentAttendance.objects.none()

#     def get_serializer_context(self):
#         return {"request": self.request}

#     def perform_create(self, serializer):
#         serializer.save(taken_by=self.request.user)

#     # ✅ ADD THIS FUNCTION BELOW
#     def get_all_attendance_for_privileged_users(self):
#         """
#         Custom function to be called internally or from a separate view
#         to return full attendance for admin, dean, vpa, vpi only.
#         """
#         user = self.request.user
#         user_type = getattr(user, "user_type", None)

#         if user_type in ['admin', 'dean', 'vpa', 'vpi']:
#             return StudentAttendance.objects.select_related("student", "grade_class", "student__user").order_by("-date")
        
#         return StudentAttendance.objects.none()








class BulkCreateStudentAttendanceView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTakeAttendance]

    def post(self, request, *args, **kwargs):
        print("Received data:", request.data)  # Debug print
        serializer = StudentAttendanceSerializer(data=request.data, many=True, context={'request': request})
        if serializer.is_valid():
            serializer.save(taken_by=request.user)
            return Response({"message": "Attendance records created successfully."}, status=status.HTTP_201_CREATED)
        print("Validation errors:", serializer.errors)  # Debug print errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



