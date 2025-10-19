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
        grade_class = self.request.query_params.get("grade_class")
        academic_year = self.request.query_params.get("academic_year")

        queryset = StudentAdmission.objects.filter(status="Enrolled")

        if grade_class:
            queryset = queryset.filter(grade_class_id=grade_class)
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return queryset





class GradeDistributionListView(viewsets.ModelViewSet):
    """
    Handles grade distribution records.
    Teachers can add grades; Admin/VPI/VPA have full access.
    Sends notifications to both students and leadership roles.
    """
    queryset = GradeDistribution.objects.none()
    serializer_class = GradeDistributionSerializer
    permission_classes = [IsAuthenticated]

    # ------------------------ GET QUERYSET ------------------------ #
    def get_queryset(self):
        user = self.request.user
        year_id = self.request.query_params.get("academic_year")
        queryset = GradeDistribution.objects.all()

        # Filter by academic year (default to active)
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        else:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if active_year:
                queryset = queryset.filter(academic_year=active_year)

        # Permissions: admin/vpi/vpa see all
        if user.user_type in ['admin', 'vpi', 'vpa']:
            pass

        # Teachers see only their assigned classes and subjects
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
                logger.warning(f"No TeacherDataProcess record found for {user.email}")
                return GradeDistribution.objects.none()

        else:
            # Students and others not allowed
            return GradeDistribution.objects.none()

        # Optional filtering by grade_class (ID or name)
        grade_class = self.request.query_params.get("grade_class")
        if grade_class:
            if grade_class.isdigit():
                queryset = queryset.filter(grade_class_id=int(grade_class))
            else:
                queryset = queryset.filter(grade_class__name=grade_class)

        return queryset

    # ------------------------ CREATE (Teacher submits grades) ------------------------ #
    def perform_create(self, serializer):
        user = self.request.user

        # Only teachers, admin, vpi, vpa can create
        if user.user_type not in ['teacher', 'admin', 'vpi', 'vpa']:
            raise ValidationError("You are not authorized to create grades.")

        # Assign active academic year
        active_year = AcademicYear.objects.filter(is_active=True).first()
        if not active_year:
            raise ValidationError("No active academic year found.")

        grade_distribution = serializer.save(academic_year=active_year)

        # ----------------- SEND NOTIFICATIONS ----------------- #
        try:
            # 1?? Notify students in the same class (active academic year only)
            student_users = User.objects.filter(
                user_type='student',
                admissions__grade_class=grade_distribution.grade_class,
                admissions__academic_year=active_year,
                admissions__status='Enrolled'
            ).distinct()

            for student in student_users:
                Notification.objects.create(
                    user=student,
                    message=(
                        f"Your teacher {user.username} has submitted new grades "
                        f"for {grade_distribution.subject.name} ({grade_distribution.grade_class.name}) for "
                        f"{grade_distribution.period.name}.  "
                        f"Please See the Teacher For Details or check your Grade Performance Chart! Thank You."
                    ),
                    is_read=False,
                    created_at=timezone.now()
                )

            # 2?? Notify admin, VPI, and VPA that this teacher submitted grades
            leadership_users = User.objects.filter(user_type__in=['admin', 'vpi', 'vpa'])
            for leader in leadership_users:
                Notification.objects.create(
                    user=leader,
                    message=(
                        f"Teacher {user.username} has submitted grades for "
                        f"{grade_distribution.subject.name} ({grade_distribution.grade_class.name}). "
                        f"{grade_distribution.period.name}"
                        f"Please Check. Thank You!"
                    ),
                    is_read=False,
                    created_at=timezone.now()
                )

            logger.info(f"Notifications sent for GradeDistribution by {user.email}")

        except Exception as e:
            logger.error(f"Error sending notifications after grade submission: {e}", exc_info=True)

    # ------------------------ UPDATE ------------------------ #
    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        # Full access for admin, VPI, VPA
        if user.user_type in ['admin', 'vpi', 'vpa']:
            serializer.save()
            return

        # Teachers can update only if allowed
        if user.user_type == 'teacher':
            if getattr(instance, 'allow_teacher_update', False):
                serializer.save()
            else:
                raise ValidationError(
                    "You cannot update this grade. Admin/VPI/VPA must enable permission first."
                )
        else:
            raise ValidationError("You do not have permission to update this grade.")

    # ------------------------ DELETE ------------------------ #
    def perform_destroy(self, instance):
        user = self.request.user
        # Only Admin, VPI, VPA can delete
        if user.user_type in ['admin', 'vpi', 'vpa']:
            instance.delete()
        else:
            raise ValidationError("You do not have permission to delete this grade.")

class StudentAverageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student average scores and publishing notifications.
    """
    queryset = StudentAverage.objects.none()
    serializer_class = StudentAverageSerializer
    permission_classes = [IsAuthenticated]

    # ------------------------ QUERYSET HANDLING ------------------------ #
    def get_queryset(self):
        user = self.request.user
        year_id = self.request.query_params.get("academic_year")
        qs = StudentAverage.objects.all()

        # Filter by academic year (active year by default)
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        else:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if active_year:
                qs = qs.filter(academic_year=active_year)

        # Students see only their own published results
        if user.user_type == 'student':
            admission = user.admissions.first()
            if not admission:
                raise PermissionDenied("No admission record found for this student.")
            return qs.filter(student=admission, published=True)

        return qs

    # ------------------------ CREATE STUDENT AVERAGE ------------------------ #
    def create(self, request, *args, **kwargs):
        if request.user.user_type not in ['admin', 'teacher']:
            return Response({"error": "You are not authorized to create student averages."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if not active_year:
                return Response({"error": "No active academic year found."},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer.save(academic_year=active_year)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------ PUBLISH GRADES ------------------------ #
    @action(detail=False, methods=['post'], url_path='publish-grades')
    def publish_grades(self, request):
        if request.user.user_type not in ['admin', 'vpi', 'vpa']:
            return Response({"error": "You are not authorized to publish grades."},
                            status=status.HTTP_403_FORBIDDEN)

        period_id = request.data.get('period')
        year_id = request.data.get('academic_year')

        # Automatically use active academic year if not provided
        if not year_id:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if not active_year:
                return Response({"error": "No active academic year found."},
                                status=status.HTTP_400_BAD_REQUEST)
            year_id = active_year.id

        if not period_id:
            return Response({"error": "The 'period' field is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            period = Period.objects.get(id=period_id)
            student_averages = StudentAverage.objects.filter(
                period=period,
                student__academic_year_id=year_id,
                academic_year_id=year_id,
                published=False
            )

            if not student_averages.exists():
                return Response({"message": "No unpublished grades found for the selected period."},
                                status=status.HTTP_404_NOT_FOUND)

            # Publish grades
            student_averages.update(published=True)

            # Notify only students in the active academic year
            active_students = User.objects.filter(
                user_type='student',
                admissions__academic_year_id=year_id,
                admissions__status='Enrolled'
            ).distinct()

            for student in active_students:
                Notification.objects.create(
                    user=student,
                    message=f"Grades for {period.name} have been published. Check your Grade Report.",
                    is_read=False,
                    created_at=timezone.now()
                )

            return Response(
                {"message": f"All grades for {period.name} have been published and notifications sent to active-year students."},
                status=status.HTTP_200_OK
            )

        except Period.DoesNotExist:
            return Response({"error": "Invalid Period ID."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error publishing grades: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ------------------------ UNPUBLISH GRADES ------------------------ #
    @action(detail=False, methods=['post'], url_path='unpublish-grades')
    def unpublish_grades(self, request):
        if request.user.user_type != 'admin':
            return Response({"error": "You are not authorized to unpublish grades."},
                            status=status.HTTP_403_FORBIDDEN)

        period_id = request.data.get('period')
        year_id = request.data.get('academic_year')

        # Auto-detect active academic year
        if not year_id:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if not active_year:
                return Response({"error": "No active academic year found."},
                                status=status.HTTP_400_BAD_REQUEST)
            year_id = active_year.id

        if not period_id:
            return Response({"error": "The 'period' field is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            period = Period.objects.get(id=period_id)
            student_averages = StudentAverage.objects.filter(
                period=period,
                student__academic_year_id=year_id,
                academic_year_id=year_id,
                published=True
            )

            if not student_averages.exists():
                return Response({"message": "No published grades found for the selected period."},
                                status=status.HTTP_404_NOT_FOUND)

            student_averages.update(published=False)

            return Response(
                {"message": f"All grades for {period.name} have been unpublished successfully."},
                status=status.HTTP_200_OK
            )

        except Period.DoesNotExist:
            return Response({"error": "Invalid Period ID."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error unpublishing grades: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ------------------------ CLASS REPORT ------------------------ #
    @action(detail=False, methods=['post'], url_path='class-report')
    def class_report(self, request):
        grade_class_id = request.data.get("grade_class")
        period_id = request.data.get("period")
        year_id = request.data.get("academic_year")

        if not grade_class_id or not period_id:
            return Response({"error": "Grade class and period are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Default to active academic year if not provided
        if not year_id:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if not active_year:
                return Response({"error": "No active academic year found."},
                                status=status.HTTP_400_BAD_REQUEST)
            year_id = active_year.id

        try:
            students = StudentAdmission.objects.filter(
                grade_class_id=grade_class_id,
                academic_year_id=year_id,
                status="Enrolled"
            )

            if not students.exists():
                return Response({"error": "No students found in this grade class for the selected year."},
                                status=status.HTTP_404_NOT_FOUND)

            # Ensure StudentAverage exists for each enrolled student
            for student in students:
                if not StudentAverage.objects.filter(
                    student=student,
                    period_id=period_id,
                    academic_year_id=year_id
                ).exists():
                    try:
                        StudentAverage.objects.create(
                            student=student,
                            grade_class=student.grade_class,
                            period_id=period_id,
                            academic_year_id=year_id,
                            published=False
                        )
                    except Exception as e_inner:
                        logger.error(f"Failed to create StudentAverage for student {student.id}: {e_inner}")
                        return Response(
                            {"error": f"Failed to create StudentAverage for student {student.id}: {e_inner}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

            # Fetch student averages for the report
            student_averages = StudentAverage.objects.filter(
                student__in=students,
                period_id=period_id,
                academic_year_id=year_id
            ).order_by('student', '-id')

            # Remove duplicates
            unique = {}
            for avg in student_averages:
                if avg.student_id not in unique:
                    unique[avg.student_id] = avg

            serializer = StudentAverageSerializer(unique.values(), many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating class report: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Error generating class report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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


# class StudentsInGradeClassView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, grade_class_id):
#         students = StudentAdmission.objects.filter(grade_class_id=grade_class_id)
#         return Response(StudentAdmissionSerializer(students, many=True).data)



class StudentsInGradeClassView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, grade_class_id):
        academic_year_id = request.query_params.get('academic_year')
        
        if academic_year_id is None:
            return Response({"error": "academic_year parameter is required."}, status=400)

        try:
            students = StudentAdmission.objects.filter(
                grade_class_id=grade_class_id,
                academic_year_id=academic_year_id
            )
            serializer = StudentAdmissionSerializer(students, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)






class AcademicReportView(APIView):
    """
    Returns:
    - Honor & delinquent students for a grade class and period.
    - Honor students grouped by category with ranks.
    - Top honor student for the period.
    Aggregates multiple entries per student into one.
    """

    def get(self, request, grade_class_id, period_id):
        try:
            grade_class = GradeClass.objects.get(id=grade_class_id)
            period = Period.objects.get(id=period_id)
        except GradeClass.DoesNotExist:
            return Response({"detail": "Grade Class not found."}, status=status.HTTP_404_NOT_FOUND)
        except Period.DoesNotExist:
            return Response({"detail": "Period not found."}, status=status.HTTP_404_NOT_FOUND)

        student_averages = StudentAverage.objects.filter(
            grade_class=grade_class,
            period=period,
            published=True
        )

        # Aggregate scores by student
        student_dict = {}
        for sa in student_averages:
            student_id = sa.student.id
            if student_id not in student_dict:
                student_dict[student_id] = {
                    "student_name": sa.student.full_name,
                    "total": 0,
                    "count": 0,
                    "formatted_remarks": []
                }
            student_dict[student_id]["total"] += sa.formatted_average_score()
            student_dict[student_id]["count"] += 1
            student_dict[student_id]["formatted_remarks"].append(sa.get_remark())

        honor_students = []
        delinquent_students = []

        # Build final list per student
        for idx, (student_id, info) in enumerate(student_dict.items(), start=1):
            avg = info["total"] / info["count"] if info["count"] else 0
            remark = info["formatted_remarks"][0] if info["formatted_remarks"] else ""
            student_data = {
                "student_id": student_id,
                "student_name": info["student_name"],
                "average": round(avg, 2),
                "remark": remark,
                "rank": idx
            }

            if avg >= 80:
                honor_students.append(student_data)
            elif avg < 70:
                delinquent_students.append(student_data)

        # Sort honor students by average descending
        honor_students_sorted = sorted(honor_students, key=lambda x: x['average'], reverse=True)
        # Re-assign ranks after sorting
        for idx, student in enumerate(honor_students_sorted, start=1):
            student["rank"] = idx

        # Group honor students by category
        honor_groups = {
            "Principal's List (90-100)": [],
            "High Honor Roll (85-89)": [],
            "Honor Roll (80-84)": [],
        }
        for student in honor_students_sorted:
            avg = student['average']
            if avg >= 90:
                honor_groups["Principal's List (90-100)"].append(student)
            elif 85 <= avg <= 89:
                honor_groups["High Honor Roll (85-89)"].append(student)
            elif 80 <= avg <= 84:
                honor_groups["Honor Roll (80-84)"].append(student)

        top_student = honor_students_sorted[0] if honor_students_sorted else None

        response_data = {
            "grade_class": grade_class.name,
            "period": period.name,
            "honor_students": honor_students_sorted,
            "delinquent_students": delinquent_students,
            "total_honor_students": len(honor_students_sorted),
            "total_delinquent_students": len(delinquent_students),
            "honor_groups": honor_groups,
            "top_honor_student": top_student,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class AcademicReportAllView(APIView):
    """
    Returns academic report for ALL grade classes for a given period.
    """

    def get(self, request, period_id):
        try:
            period = Period.objects.get(id=period_id)
        except Period.DoesNotExist:
            return Response({"detail": "Period not found."}, status=404)

        grade_classes = GradeClass.objects.all()
        all_reports = []

        for gc in grade_classes:
            student_averages = StudentAverage.objects.filter(
                grade_class=gc,
                period=period,
                published=True
            )

            # Aggregate scores per student
            student_dict = {}
            for sa in student_averages:
                student_id = sa.student.id
                if student_id not in student_dict:
                    student_dict[student_id] = {
                        "student_name": sa.student.full_name,
                        "total": 0,
                        "count": 0,
                        "formatted_remarks": []
                    }
                student_dict[student_id]["total"] += sa.formatted_average_score()
                student_dict[student_id]["count"] += 1
                student_dict[student_id]["formatted_remarks"].append(sa.get_remark())

            honor_students = []
            delinquent_students = []

            for idx, (student_id, info) in enumerate(student_dict.items(), start=1):
                avg = info["total"] / info["count"] if info["count"] else 0
                remark = info["formatted_remarks"][0] if info["formatted_remarks"] else ""
                student_data = {
                    "student_id": student_id,
                    "student_name": info["student_name"],
                    "average": round(avg, 2),
                    "remark": remark,
                    "rank": idx
                }

                if avg >= 80:
                    honor_students.append(student_data)
                elif avg < 70:
                    delinquent_students.append(student_data)

            # Sort and assign ranks
            honor_students_sorted = sorted(honor_students, key=lambda x: x['average'], reverse=True)
            for idx, student in enumerate(honor_students_sorted, start=1):
                student["rank"] = idx

            # Honor groups
            honor_groups = {
                "Principal's List (90-100)": [],
                "High Honor Roll (85-89)": [],
                "Honor Roll (80-84)": [],
            }
            for student in honor_students_sorted:
                avg = student['average']
                if avg >= 90:
                    honor_groups["Principal's List (90-100)"].append(student)
                elif 85 <= avg <= 89:
                    honor_groups["High Honor Roll (85-89)"].append(student)
                elif 80 <= avg <= 84:
                    honor_groups["Honor Roll (80-84)"].append(student)

            top_student = honor_students_sorted[0] if honor_students_sorted else None

            all_reports.append({
                "grade_class": gc.name,
                "period": period.name,
                "honor_students": honor_students_sorted,
                "delinquent_students": delinquent_students,
                "total_honor_students": len(honor_students_sorted),
                "total_delinquent_students": len(delinquent_students),
                "honor_groups": honor_groups,
                "top_honor_student": top_student,
            })

        return Response(all_reports, status=200)








