from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import permissions
from rest_framework import filters
from academics.serializers import SubjectSerializer
from notifications.models import Notification
from users.models import User
from .models import SupportStaff, TeacherLessonPlan
from .serializers import SupportStaffSerializer, TeacherLessonPlanSerializer, TeacherSubjectsSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from teacherdata.models import TeacherDataProcess



class TeacherSubjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            teacher = TeacherDataProcess.objects.get(username=user)
            subjects = teacher.subjects.all()
            subject_serializer = SubjectSerializer(subjects, many=True)

            # Existing string list for grade_class
            grade_classes_str = [str(g) for g in teacher.grade_class.all()]

            # New list with id + name for dropdown
            grade_classes_data = [{"id": g.id, "name": g.name} for g in teacher.grade_class.all()]

            additional_info = {
                "qualification": teacher.qualification,
                "division": str(teacher.division),
                "grade_class": grade_classes_str,
                "dependent_student": teacher.dependent_student,
                "salary": teacher.salary,
            }

            return Response({
                "teacher_id": teacher.id,  # ✅ Add this
                "subjects": subject_serializer.data,
                "grade_classes": grade_classes_data,
                "teacher_info": additional_info
            })

        except TeacherDataProcess.DoesNotExist:
            return Response({
                "teacher_id": None,
                "subjects": [],
                "grade_classes": [],
                "teacher_info": {}
            }, status=200)


     
        

class SupportStaffViewSet(viewsets.ModelViewSet):
    queryset = SupportStaff.objects.all()
    serializer_class = SupportStaffSerializer
    parser_classes = (MultiPartParser, FormParser)


class IsAdminVPIOrVPAOrOwner(permissions.BasePermission):
    """
    Custom permission:
    - Admin/VPI/VPA can view, edit, delete any lesson plan.
    - Teachers can only view/edit/delete their own lesson plan.
    """

    def has_object_permission(self, request, view, obj):
        user_type = getattr(request.user, 'user_type', None)
        if user_type in ['admin', 'vpi', 'vpa']:
            return True
        return obj.teacher == request.user

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated



class IsAdminVPIOrVPAOrOwner(permissions.BasePermission):
    """
    Allow admin, vpi, vpa to view/edit/delete all lesson plans.
    Teachers can only view/edit/delete their own.
    Admin/VPI/VPA do NOT need to be linked to TeacherDataProcess.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        user_type = getattr(user, 'user_type', None)

        if user_type in ['admin', 'vpi', 'vpa']:
            return True
        
        if user_type == 'teacher':
            return obj.teacher == user

        return False

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated





class TeacherLessonPlanViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherLessonPlanSerializer
    permission_classes = [IsAuthenticated]  # Add your custom permission if needed

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['admin', 'vpi', 'vpa', 'dean']:
            return TeacherLessonPlan.objects.all()
        elif user.user_type == 'teacher':
            return TeacherLessonPlan.objects.filter(teacher=user)
        return TeacherLessonPlan.objects.none()

    def perform_create(self, serializer):
        # Save the lesson plan with the teacher set to the current user
        lesson_plan = serializer.save(teacher=self.request.user)

        # Define which user roles should receive the notification
        notify_roles = ['admin', 'vpi', 'vpa', 'dean']

        # Get all users with those roles (whether active or not)
        recipients = User.objects.filter(user_type__in=notify_roles)

        # Loop through and create a general notification for each
        for recipient in recipients:
            Notification.create_general_notification(
                user=recipient,
                message=f"{self.request.user.username} has submitted a new lesson plan."
            )

        # Optional debug print (remove in production)
        print(f"? Lesson plan submitted by {self.request.user.email}. Notifications sent to: {[r.email for r in recipients]}")





class TeacherSubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            teacher = TeacherDataProcess.objects.get(username=request.user)
        except TeacherDataProcess.DoesNotExist:
            return Response({"detail": "Teacher data not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = TeacherSubjectsSerializer(teacher)
        return Response(serializer.data)
    





