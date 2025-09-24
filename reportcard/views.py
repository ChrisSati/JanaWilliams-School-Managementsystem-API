from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
import logging

from teacherdata.models import TeacherDataProcess
from users.models import User
from academics.models import GradeClass, StudentAdmission, Subject
from academics.serializers import GradeClassSerializer, StudentAdmissionSerializer, SubjectSerializer
from notifications.models import Notification
from .models import GradeDistribution, GradesReport, Period, StudentAverage
from .serializers import (
    GradeDistributionSerializer,
    GradesReportSerializer,
    PeriodSerializer,
    StudentAverageSerializer,
    StudentGradeChartSerializer,
)
from academicyear.models import AcademicYear

logger = logging.getLogger(__name__)


class PeriodViewSet(viewsets.ModelViewSet):
    queryset = Period.objects.all()
    serializer_class = PeriodSerializer
    permission_classes = [IsAuthenticated]


class FilterStudentsByGradeClassView(generics.ListAPIView):
    serializer_class = StudentAdmissionSerializer

    def get_queryset(self):
        grade_class = self.request.query_params.get("grade_class", None)
        if grade_class:
            return StudentAdmission.objects.filter(grade_class=grade_class, status="Enrolled")
        return StudentAdmission.objects.none()


class GradeDistributionListView(viewsets.ModelViewSet):
    queryset = GradeDistribution.objects.none()
    serializer_class = GradeDistributionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        year_id = self.request.query_params.get("academic_year")
        queryset = GradeDistribution.objects.all()

        # Filter by academic year
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        else:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if active_year:
                queryset = queryset.filter(academic_year=active_year)

        # Admin, VPI, VPA: see all grades
        if user.user_type in ['admin', 'vpi', 'vpa']:
            pass
        # Teachers: see only assigned classes and subjects
        elif user.user_type == 'teacher':
            try:
                teacher_data = TeacherDataProcess.objects.get(username=user)
                assigned_classes = teacher_data.grade_class.all()
                assigned_subjects = teacher_data.subjects.all()
                queryset = queryset.filter(
                    grade_class__in=assigned_classes,
                    subject__in=assigned_subjects
                )
            except TeacherDataProcess.DoesNotExist:
                return GradeDistribution.objects.none()
        else:
            return GradeDistribution.objects.none()

        # Optional filtering by grade_class (ID or name)
        grade_class = self.request.query_params.get("grade_class")
        if grade_class:
            if grade_class.isdigit():
                queryset = queryset.filter(grade_class_id=int(grade_class))
            else:
                queryset = queryset.filter(grade_class__name=grade_class)

        return queryset

    def perform_create(self, serializer):
        # Auto-assign active academic year
        active_year = AcademicYear.objects.filter(is_active=True).first()
        if not active_year:
            raise ValidationError("No active academic year found.")
        serializer.save(academic_year=active_year)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        # Full access: Admin, VPI, VPA
        if user.user_type in ['admin', 'vpi', 'vpa']:
            serializer.save()
            return

        # Teacher can update only if allow_teacher_update checkbox is True
        if user.user_type == 'teacher':
            if getattr(instance, 'allow_teacher_update', False):
                serializer.save()
            else:
                raise ValidationError("You cannot update this grade. Admin/VPI/VPA must enable permission first.")
        else:
            raise ValidationError("You do not have permission to update this grade.")

    def perform_destroy(self, instance):
        user = self.request.user
        # Only Admin, VPI, VPA can delete
        if user.user_type in ['admin', 'vpi', 'vpa']:
            instance.delete()
        else:
            raise ValidationError("You do not have permission to delete this grade.")


class StudentAverageViewSet(viewsets.ModelViewSet):
    queryset = StudentAverage.objects.none()
    serializer_class = StudentAverageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        year_id = self.request.query_params.get("academic_year")
        qs = StudentAverage.objects.all()

        # Filter by academic year
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        else:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if active_year:
                qs = qs.filter(academic_year=active_year)

        if user.user_type == 'student':
            admission = user.admissions.first()
            if not admission:
                raise PermissionDenied("No admission record found for the student.")
            return qs.filter(student=admission, published=True)

        return qs

    def create(self, request, *args, **kwargs):
        if request.user.user_type not in ['admin', 'teacher']:
            return Response({"error": "You are not authorized to create student averages."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Auto-assign active academic year
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if not active_year:
                return Response({"error": "No active academic year found."}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(academic_year=active_year)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='publish-grades')
    def publish_grades(self, request):
        if request.user.user_type not in ['admin', 'vpi', 'vpa']:
            return Response({"error": "You are not authorized to publish grades."}, status=status.HTTP_403_FORBIDDEN)

        period_id = request.data.get('period')
        year_id = request.data.get('academic_year')
        if not period_id or not year_id:
            return Response({"error": "Both period and academic_year are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            period = Period.objects.get(id=period_id)
            student_averages = StudentAverage.objects.filter(
                period=period, academic_year_id=year_id, published=False
            )

            if not student_averages.exists():
                return Response({"message": "No unpublished grades found for the selected period."}, status=status.HTTP_404_NOT_FOUND)

            student_averages.update(published=True)

            students = User.objects.filter(user_type='student')
            for student in students:
                Notification.objects.create(
                    user=student,
                    message=f"Grades for {period.name} ({period.academic_year}) have been published. Check Your Grade Report.",
                    is_read=False,
                    created_at=timezone.now()
                )

            return Response({"message": "All grades for the selected period have been published and notifications sent."}, status=status.HTTP_200_OK)

        except Period.DoesNotExist:
            return Response({"error": "Invalid Period ID."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error publishing grades: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='unpublish-grades')
    def unpublish_grades(self, request):
        if request.user.user_type != 'admin':
            return Response({"error": "You are not authorized to unpublish grades."}, status=status.HTTP_403_FORBIDDEN)

        period_id = request.data.get('period')
        year_id = request.data.get('academic_year')
        if not period_id or not year_id:
            return Response({"error": "Both period and academic_year are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            period = Period.objects.get(id=period_id)
            student_averages = StudentAverage.objects.filter(
                period=period, academic_year_id=year_id, published=True
            )

            if not student_averages.exists():
                return Response({"message": "No published grades found for the selected period."}, status=status.HTTP_404_NOT_FOUND)

            student_averages.update(published=False)

            Notification.objects.filter(
                message__icontains=f"Grades for {period.name}"
            ).delete()

            return Response({"message": "All grades for the selected period have been unpublished and notifications removed."}, status=status.HTTP_200_OK)

        except Period.DoesNotExist:
            return Response({"error": "Invalid Period ID."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error unpublishing grades: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='class-report')
    def class_report(self, request):
        grade_class_id = request.data.get("grade_class")
        period_id = request.data.get("period")
        year_id = request.data.get("academic_year")

        if not grade_class_id or not period_id or not year_id:
            return Response({"error": "Grade class, period and academic_year are required."}, status=status.HTTP_400_BAD_REQUEST)

        students = StudentAdmission.objects.filter(
            grade_class_id=grade_class_id, status="Enrolled", academic_year_id=year_id
        )
        if not students.exists():
            return Response({"error": "No students found in this grade class for the selected year."}, status=status.HTTP_404_NOT_FOUND)

        student_averages = StudentAverage.objects.filter(
            student__in=students, period_id=period_id, academic_year_id=year_id
        ).order_by('student', '-id')

        unique = {}
        for avg in student_averages:
            if avg.student_id not in unique:
                unique[avg.student_id] = avg

        serializer = StudentAverageSerializer(unique.values(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GradesReportViewSet(viewsets.ModelViewSet):
    queryset = GradesReport.objects.none()
    serializer_class = GradesReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        student_id = self.request.query_params.get("student")
        academic_year = self.request.query_params.get("academic_year")

        queryset = GradesReport.objects.all()

        # Filter by academic_year if provided
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        else:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if active_year:
                queryset = queryset.filter(academic_year=active_year)

        # Admin, VPI, VPA, Dean -> full access
        if user.user_type in ["admin", "vpi", "vpa", "dean"]:
            if student_id:
                queryset = queryset.filter(student_id=student_id)
            return queryset

        # Teachers -> only their assigned classes
        if user.user_type == "teacher":
            assigned_grade_classes = TeacherDataProcess.objects.filter(
                username=user
            ).values_list("grade_class", flat=True)

            allowed_students = StudentAdmission.objects.filter(
                grade_class_id__in=assigned_grade_classes
            ).values_list("id", flat=True)

            if student_id:
                if int(student_id) in allowed_students:
                    queryset = queryset.filter(student_id=student_id)
                else:
                    return GradesReport.objects.none()
            else:
                queryset = queryset.filter(student_id__in=allowed_students)

            return queryset

        # Students -> only their own reports
        if user.user_type == "student":
            queryset = queryset.filter(student__user=user)
            return queryset

        # Parents -> only their children
        if user.user_type == "parent":
            queryset = queryset.filter(student__parent=user)
            return queryset

        return GradesReport.objects.none()

    @action(detail=True, methods=["get"])
    def period_grades(self, request, pk=None):
        report = self.get_object()
        period_grades = report.get_student_grades()
        if not period_grades:
            return Response({"detail": "No grades available."}, status=404)
        return Response(period_grades, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_grade_performance(request):
    user = request.user
    try:
        student = user.admissions.first()
        if not student:
            return Response([], status=200)

        subject = request.GET.get("subject")
        period = request.GET.get("period")

        grades = GradeDistribution.objects.filter(student=student)

        if subject:
            grades = grades.filter(subject__name=subject)
        if period:
            grades = grades.filter(period__name=period)

        serializer = StudentGradeChartSerializer(grades, many=True)
        return Response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


class AssignedGradeClassesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type == 'admin':
            classes = GradeClass.objects.all()
        else:
            try:
                teacher = TeacherDataProcess.objects.get(username=user)
                classes = teacher.grade_class.all()
            except TeacherDataProcess.DoesNotExist:
                classes = GradeClass.objects.none()
        return Response(GradeClassSerializer(classes, many=True).data)


class AssignedSubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type == 'admin':
            subjects = Subject.objects.all()
        else:
            try:
                teacher = TeacherDataProcess.objects.get(username=user)
                subjects = teacher.subjects.all()
            except TeacherDataProcess.DoesNotExist:
                subjects = Subject.objects.none()
        return Response(SubjectSerializer(subjects, many=True).data)


class StudentsInGradeClassView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, grade_class_id):
        students = StudentAdmission.objects.filter(grade_class_id=grade_class_id)
        return Response(StudentAdmissionSerializer(students, many=True).data)
