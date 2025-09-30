from django.shortcuts import render
from django.core.mail import send_mail
from rest_framework import serializers
from threading import Thread
import json
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from payroll.models import Payroll
from academics.models import StudentAdmission, Subject
from notifications.models import Notification
from academics.serializers import StudentAdmissionSerializer
from users.models import User
from teacherdata.models import TeacherDataProcess, TeacherLessonPlan
from teacherdata.serializers import TeacherDataProcessSerializer
from .models import Assignment, AssignmentLike, AssignmentComment, OnlineTest, PeriodicTest, Question, StudentAnswer, TestQuestion
from .serializers import AssignmentCommentSerializer, AssignmentSerializer, CommentCreateSerializer, OnlineTestSerializer, PeriodicTestSerializer, QuestionSerializer, StudentAnswerSerializer, TestQuestionSerializer, ReplyCreateSerializer, AssignmentReplySerializer
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q, F
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action



class AssignmentViewSet(viewsets.ModelViewSet):
    """CRUD + social actions for assignments."""
    queryset = Assignment.objects.none()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    # -------- Queryset w/ counts & role scoping --------
    def get_queryset(self):
        user = self.request.user
        qs = Assignment.objects.all().select_related('teacher', 'subject', 'grade_class')

        # Teacher: show *only* assignments they created
        if getattr(user, 'user_type', None) == 'teacher':
            qs = qs.filter(teacher=user)

        # Student: show assignments for all their enrolled grade classes
        elif getattr(user, 'user_type', None) == 'student':
            grade_class_ids = user.admissions.filter(status='Enrolled').values_list('grade_class_id', flat=True)
            if grade_class_ids:
                qs = qs.filter(grade_class_id__in=grade_class_ids)
            else:
                qs = qs.none()

        # Parent: show assignments for any child's enrolled grade class
        elif getattr(user, 'user_type', None) == 'parent':
            child_grade_ids = user.children.filter(status='Enrolled').values_list('grade_class_id', flat=True)
            if child_grade_ids:
                qs = qs.filter(grade_class_id__in=child_grade_ids)
            else:
                qs = qs.none()

        # else: admin/staff see all assignments

        # Annotate interaction counts
        qs = qs.annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', filter=Q(comments__parent__isnull=True), distinct=True),
            replies_count=Count('comments', filter=Q(comments__parent__isnull=False), distinct=True),
        ).annotate(total_comment_items=F('comments_count') + F('replies_count'))

        return qs.order_by('-created_at')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    # -------- Create w/ teacher inject + notifications --------
    def perform_create(self, serializer):
        assignment = serializer.save(teacher=self.request.user)
        self._notify_students_and_parents(assignment)
        self._notify_students_and_parents_detailed(assignment)

    # -------- Helpers: permissions & notifications --------
    def _assert_user_can_interact(self, assignment, user=None):
        user = user or self.request.user
        user_type = getattr(user, 'user_type', None)

        if user_type == 'teacher':
            if assignment.teacher_id == user.id:
                return True
            return TeacherDataProcess.objects.filter(
                teacher=user,
                grade_class=assignment.grade_class,
                subject=assignment.subject,
                is_active=True,
            ).exists()

        if user_type == 'student':
            grade_class_ids = user.admissions.filter(status='Enrolled').values_list('grade_class_id', flat=True)
            return assignment.grade_class_id in grade_class_ids

        if user_type == 'parent':
            return user.children.filter(grade_class=assignment.grade_class, status='Enrolled').exists()

        # staff/admin fallback
        return True

    def _notify_students_and_parents(self, assignment):
        grade_class = assignment.grade_class
        students_qs = getattr(grade_class, 'students', StudentAdmission.objects.none()).select_related('user')
        student_users = [s.user for s in students_qs if getattr(s, 'user', None)]

        parent_users = []
        for s in students_qs.prefetch_related('parents'):
            parent_users.extend(list(s.parents.all()))

        msg = (
            f"New assignment posted: {assignment.title} for "
            f"{assignment.grade_class_name} / {assignment.subject_name}. Due {assignment.due_date}."
        )

        ids = set()
        everyone = []
        for u in student_users + parent_users:
            if u and u.id not in ids:
                ids.add(u.id)
                everyone.append(u)

        Notification.objects.bulk_create([
            Notification(user=u, message=msg) for u in everyone
        ])

    def _notify_students_and_parents_detailed(self, assignment):
        students = StudentAdmission.objects.filter(grade_class=assignment.grade_class).select_related('user')

        parent_ids = students.values_list('parent_id', flat=True)
        parents = User.objects.filter(id__in=parent_ids, user_type='parent')

        for student in students:
            if getattr(student, 'user_id', None):
                Notification.objects.create(
                    user=student.user,
                    message=(
                        f"A new assignment '{assignment.title}' has been posted for "
                        f"{assignment.subject.name}. Due: {assignment.due_date}."
                    )
                )

        for parent in parents:
            Notification.objects.create(
                user=parent,
                message=(
                    f"A new assignment '{assignment.title}' has been posted in "
                    f"{assignment.grade_class.name} for subject {assignment.subject.name}."
                )
            )

    # -------- LIKE (toggle) --------
    @action(detail=True, methods=['post'], url_path='like')
    def like(self, request, pk=None):
        assignment = self.get_object()
        if not self._assert_user_can_interact(assignment):
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        obj, created = AssignmentLike.objects.get_or_create(assignment=assignment, user=request.user)
        if not created:
            obj.delete()
            return Response({'liked': False})
        return Response({'liked': True})

    # -------- COMMENTS (list + create top-level) --------
    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, pk=None):
        assignment = self.get_object()

        if request.method == 'GET':
            qs = assignment.comments.filter(parent__isnull=True).select_related('user').prefetch_related('replies__user')
            ser = AssignmentCommentSerializer(qs, many=True, context={'request': request})
            return Response(ser.data)

        if not self._assert_user_can_interact(assignment):
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        ser = CommentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        comment = AssignmentComment.objects.create(
            assignment=assignment,
            user=request.user,
            content=ser.validated_data['content']
        )

        if assignment.teacher != request.user:
            Notification.objects.create(
                user=assignment.teacher,
                message=f"{request.user.username} commented on '{assignment.title}'."
            )

        out = AssignmentCommentSerializer(comment, context={'request': request}).data
        return Response(out, status=status.HTTP_201_CREATED)

    # -------- REPLY to a comment --------
    @action(detail=True, methods=['post'], url_path='comments/(?P<comment_id>[^/.]+)/reply')
    def reply(self, request, pk=None, comment_id=None):
        assignment = self.get_object()
        if not self._assert_user_can_interact(assignment):
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        parent_comment = get_object_or_404(
            AssignmentComment,
            pk=comment_id,
            assignment=assignment,
            parent__isnull=True
        )

        ser = ReplyCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reply_obj = AssignmentComment.objects.create(
            assignment=assignment,
            user=request.user,
            parent=parent_comment,
            content=ser.validated_data['content']
        )

        if parent_comment.user != request.user:
            Notification.objects.create(
                user=parent_comment.user,
                message=f"{request.user.username} replied to your comment on '{assignment.title}'."
            )

        if assignment.teacher not in (request.user, parent_comment.user):
            Notification.objects.create(
                user=assignment.teacher,
                message=f"{request.user.username} replied under '{assignment.title}'."
            )

        out = AssignmentReplySerializer(reply_obj, context={'request': request}).data
        return Response(out, status=status.HTTP_201_CREATED)


class AssignmentCommentDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(AssignmentComment, pk=pk)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if request.user != obj.user and not request.user.is_staff:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        ser = CommentCreateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        if 'content' in ser.validated_data:
            obj.content = ser.validated_data['content']
            obj.is_edited = True
            obj.save(update_fields=['content', 'is_edited', 'updated_at'])
        return Response(AssignmentCommentSerializer(obj).data)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if request.user != obj.user and not request.user.is_staff:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





class OnlineTestViewSet(viewsets.ModelViewSet):
    queryset = OnlineTest.objects.all().order_by('-created_at')
    serializer_class = OnlineTestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)






class TeacherDashboardView(APIView):
    """
    Dashboard for logged-in teacher showing:
    - Personal data
    - Total salary (from TeacherDataProcess)
    - Total lesson plans
    - Total assignments
    - Total deductions (from Payroll)
    - Total salary advances (from SalaryAdvance)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Get teacher personal record (linked by OneToOneField)
        tdp_qs = TeacherDataProcess.objects.filter(username=user)
        tdp_obj = tdp_qs.first()
        tdp_data = TeacherDataProcessSerializer(tdp_obj, context={'request': request}).data if tdp_obj else None

        # Totals for salary, plans, and assignments
        total_salary = tdp_qs.aggregate(total=Sum('salary'))['total'] or 0
        lessonplan_count = TeacherLessonPlan.objects.filter(teacher=user).count()
        assignment_count = Assignment.objects.filter(teacher=user).count()

        # ? Totals for deductions and salary advance
        total_deductions = 0
        total_salary_advance = 0

        if tdp_obj:
            # All payroll records for this teacher
            payroll_aggregate = Payroll.objects.filter(teacher=tdp_obj).aggregate(
                total_deductions=Sum('deductions'),
                total_advance=Sum('salary_advance')
            )
            total_deductions = payroll_aggregate['total_deductions'] or 0
            total_salary_advance = payroll_aggregate['total_advance'] or 0

        payload = {
            'teacher_id': user.id,
            'teacher_name': getattr(user, 'full_name', user.get_username()),
            'personal_data': tdp_data,
            'total_salary': str(total_salary),
            'lessonplan_count': lessonplan_count,
            'assignment_count': assignment_count,
            'total_deductions': str(total_deductions),
            'total_salary_advance': str(total_salary_advance),
        }
        return Response(payload, status=status.HTTP_200_OK)
    






# class TestQuestionViewSet(viewsets.ModelViewSet):
#     queryset = TestQuestion.objects.all()
#     serializer_class = TestQuestionSerializer
#     permission_classes = [IsAuthenticated]


class QuestionViewSet(viewsets.ModelViewSet):
   queryset = Question.objects.all()
   serializer_class = QuestionSerializer
   permission_classes = [IsAuthenticated]



def parse_duration_hms(value: str) -> timedelta:
    """
    Accept 'HH:MM:SS' or 'H:MM:SS' and return timedelta.
    Raise ValueError for bad input.
    """
    if not value:
        raise ValueError("Duration is required.")
    parts = value.split(":")
    if len(parts) != 3:
        raise ValueError("Duration must be HH:MM:SS.")
    h, m, s = parts
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s))



def parse_duration_hms(value: str) -> timedelta:
    if not value:
        raise ValueError("Duration is required.")
    parts = value.split(":")
    if len(parts) != 3:
        raise ValueError("Duration must be HH:MM:SS.")
    h, m, s = parts
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s))


class PeriodicTestViewSet(viewsets.ModelViewSet):
    """
    Create + list + update + delete tests.

    Teachers: scoped to their own records.
    Admin/VPI/VPA: unrestricted access to all tests.
    """
    serializer_class = PeriodicTestSerializer
    permission_classes = [IsAuthenticated]

    def _get_teacher_profile(self):
        try:
            return self.request.user.teacherdataprocess
        except TeacherDataProcess.DoesNotExist:
            raise serializers.ValidationError("Teacher information is missing.")

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "user_type", None) in ["admin", "vpi", "vpa"]:
            return PeriodicTest.objects.all().order_by("-created_at")
        if getattr(user, "user_type", None) == "teacher":
            return PeriodicTest.objects.filter(teacher=user).order_by("-created_at")
        return PeriodicTest.objects.none()

    def create(self, request, *args, **kwargs):
        if request.user.user_type != "teacher":
            return Response(
                {"detail": "Only teachers can create tests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        teacher_profile = self._get_teacher_profile()
        user = request.user
        data = request.data

        # --- parse primitives
        direction = (data.get("direction") or "").strip()
        grade_class_id = data.get("grade_class")
        subject_id = data.get("subject")
        period_id = data.get("period")
        start_time = parse_datetime(data.get("start_time") or "")
        end_time = parse_datetime(data.get("end_time") or "")
        if not start_time or not end_time:
            return Response(
                {"detail": "Invalid start_time or end_time."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # duration
        try:
            duration_td = (
                parse_duration_hms(data.get("duration")) if data.get("duration") else None
            )
        except Exception as exc:
            return Response({"duration": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        # sections
        raw_sections = data.get("sections", [])
        if isinstance(raw_sections, str):
            try:
                sections_data = json.loads(raw_sections)
            except json.JSONDecodeError:
                return Response({"sections": ["Invalid JSON."]}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(raw_sections, list):
            sections_data = raw_sections
        else:
            sections_data = []

        # attach uploaded files to questions
        files = request.FILES
        for s_idx, section in enumerate(sections_data):
            for q_idx, q in enumerate(section.get("questions", [])):
                if f"question_image_{s_idx}_{q_idx}" in files:
                    q["question_image"] = files[f"question_image_{s_idx}_{q_idx}"]
                if f"attachment_{s_idx}_{q_idx}" in files:
                    q["attachment"] = files[f"attachment_{s_idx}_{q_idx}"]

        # validate assignment
        if subject_id and not teacher_profile.subjects.filter(pk=subject_id).exists():
            return Response({"subject": ["You are not assigned to this subject."]}, status=status.HTTP_400_BAD_REQUEST)
        if grade_class_id and not teacher_profile.grade_class.filter(pk=grade_class_id).exists():
            return Response({"grade_class": ["You are not assigned to this grade class."]}, status=status.HTTP_400_BAD_REQUEST)

        # payload
        serializer_payload = {
            "direction": direction,
            "grade_class": grade_class_id,
            "subject": subject_id,
            "period": period_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration_td,
            "sections": sections_data,
        }

        serializer = self.get_serializer(data=serializer_payload, context={"request": request})
        serializer.is_valid(raise_exception=True)

        test = serializer.save(teacher=user)

        # Send notifications asynchronously to avoid blocking request
        try:
            from threading import Thread
            Thread(target=self._send_notifications, args=(test,), daemon=True).start()
        except Exception as e:
            print(f"[WARN] Notification thread failed: {e}")

        response_serializer = self.get_serializer(test)
        return Response(
            {"message": "Test created successfully!", "test": response_serializer.data},
            status=status.HTTP_201_CREATED,
        )

    # ---------------- update override ----------------
    def update(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()

        if getattr(user, "user_type", None) in ["admin", "vpi", "vpa"]:
            serializer = self.get_serializer(
                instance, data=request.data, partial=kwargs.pop("partial", False)
            )
            serializer.is_valid(raise_exception=True)
            test = serializer.save()
            Thread(target=self._send_notifications, args=(test,), daemon=True).start()
            return Response({"message": "Test updated successfully!", "test": serializer.data}, status=status.HTTP_200_OK)

        teacher_profile = self._get_teacher_profile()
        if instance.teacher != user:
            return Response({"detail": "You do not have permission to edit this test."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        raw_sections = data.get("sections", [])
        if isinstance(raw_sections, str):
            try:
                data["sections"] = json.loads(raw_sections)
            except json.JSONDecodeError:
                return Response({"sections": ["Invalid JSON."]}, status=status.HTTP_400_BAD_REQUEST)

        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)

        new_subject = serializer.validated_data.get("subject", instance.subject)
        new_grade_class = serializer.validated_data.get("grade_class", instance.grade_class)
        if new_subject not in teacher_profile.subjects.all():
            return Response({"subject": ["You are not assigned to this subject."]}, status=status.HTTP_400_BAD_REQUEST)
        if new_grade_class not in teacher_profile.grade_class.all():
            return Response({"grade_class": ["You are not assigned to this grade class."]}, status=status.HTTP_400_BAD_REQUEST)

        test = serializer.save()
        Thread(target=self._send_notifications, args=(test,), daemon=True).start()

        return Response({"message": "Test updated successfully!", "test": serializer.data}, status=status.HTTP_200_OK)

    # ---------------- destroy override ----------------
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if getattr(request.user, "user_type", None) in ["admin", "vpi", "vpa"] or instance.teacher == request.user:
            self.perform_destroy(instance)
            return Response({"message": "Test deleted successfully!"}, status=204)
        return Response({"detail": "You do not have permission to delete this test."}, status=status.HTTP_403_FORBIDDEN)

    # ---------------- notifications ----------------
    def _send_notifications(self, test: PeriodicTest):
        students = StudentAdmission.objects.filter(grade_class=test.grade_class)
        student_users = [s.user for s in students if s.user]
        parent_users = [s.parent for s in students if s.parent]
        extra_staff = User.objects.filter(user_type__in=["admin", "vpi", "vpa"])
        recipients = set(student_users + parent_users + list(extra_staff))

        subject_line = f"New Test Posted: {test.subject.name}"
        msg = f"A new test for {test.subject.name} in {test.grade_class.name} has been posted by {test.teacher.username}. Available {test.start_time} - {test.end_time}."
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

        html_template = f"""
        <html><body><p>{msg}</p></body></html>
        """

        for u in recipients:
            if u.email:
                send_mail(subject_line, msg, from_email, [u.email], fail_silently=True, html_message=html_template)
            Notification.objects.create(user=u, message=msg, url=f"/tests/{test.pk}/")




class StudentAnswerViewSet(viewsets.ModelViewSet):
    queryset = StudentAnswer.objects.all().order_by('-submitted_at')
    serializer_class = StudentAnswerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)




from rest_framework.decorators import api_view, permission_classes
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_test_and_students(request):
    grade_class_id = request.query_params.get('grade_class')
    subject_id = request.query_params.get('subject')
    period_id = request.query_params.get('period')

    if not grade_class_id or not subject_id or not period_id:
        return Response({"error": "Missing parameters"}, status=400)

    try:
        test = PeriodicTest.objects.get(grade_class_id=grade_class_id, subject_id=subject_id, period_id=period_id)
    except PeriodicTest.DoesNotExist:
        return Response({"error": "Test not found"}, status=404)

    # Assuming Subject is a model, get subject name
    subject = Subject.objects.filter(id=subject_id).first()
    subject_name = subject.name if subject else ""

    # Filter students by grade_class, enrolled status, and major_subject matches selected subject name
    students = StudentAdmission.objects.filter(
        grade_class_id=grade_class_id,
        status='Enrolled',
        major_subject__iexact=subject_name
    )

    test_data = PeriodicTestSerializer(test).data
    students_data = StudentAdmissionSerializer(students, many=True).data

    return Response({
        "test": test_data,
        "students": students_data,
    })
