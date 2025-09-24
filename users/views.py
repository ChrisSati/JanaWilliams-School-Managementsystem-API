from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils import timezone
from django.db.models import Q
from rest_framework.filters import SearchFilter
from django.db.models import Max
from datetime import datetime, timedelta
from django.http import JsonResponse
from rest_framework import viewsets, filters
from rest_framework.authtoken.models import Token
from django.db import models
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework import serializers, views, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import viewsets
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from academics.models import  Division, GradeClass, StudentAdmission,  Subject, Assignment
from academics.serializers import  DivisionSerializer, GradeClassSerializer, StudentAdmissionDetailSerializer, StudentAdmissionSerializer, SubjectCountByDivisionSerializer, SubjectSerializer, AssignmentSerializer
from expenditure.models import Expenditure
from expenditure.serializers import ExpenditureSerializer
from loan.models import Loan
from loan.serializers import LoanSerializer

from notifications.models import Notification
from complaint.models import Complaint
from reportcard.models import StudentAverage
from reportcard.serializers import StudentAverageSerializer
from payroll.models import Payroll
from payroll.serializers import PayrollSerializer
from scoolfeedata.models import Payment, SchoolFeesData
from scoolfeedata.serializers import PaymentSerializer, SchoolFeesDataSerializer
from teachersalary.models import StaffSalary
from teachersalary.serializers import StaffSalarySerializer
from teacherdata.models import SupportStaff, TeacherDataProcess
from teacherdata.serializers import SupportStaffSerializer, TeacherDataProcessSerializer
from users.serializers import CustomTokenObtainPairSerializer, LoginSerializer, ProfileImageSerializer, RegisterSerializer, UserSerializer
from rest_framework import viewsets, permissions
from rest_framework import generics
from users.models import User
from academicyear.models import AcademicYear
from rest_framework.pagination import PageNumberPagination
import logging
logger = logging.getLogger(__name__)
from rest_framework import permissions, status, views


class AdminResetPasswordView(views.APIView):
    permission_classes = [permissions.IsAdminUser]  # only admins can access

    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        new_password = request.data.get("new_password")

        if not user_id or not new_password:
            return Response(
                {"error": "user_id and new_password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password)  # password hashing
            user.save()
            return Response(
                {"message": f"Password for {user.email} reset successfully"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    permission_classes = [IsAuthenticated]


class UpdateProfileImageView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ProfileImageSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile image updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DivisionViewSet(viewsets.ModelViewSet):
    queryset = Division.objects.all()
    serializer_class = DivisionSerializer
    permission_classes = [IsAuthenticated]
   

class SubjectRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class SubjectCountView(APIView):
    def get(self, request):
        count = Subject.total_subject_count()
        return Response({'total_subject_count': count})



class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    # permission_classes = [permissions.IsAuthenticated]





class SchoolFeesDataViewSet(ModelViewSet):
    queryset = SchoolFeesData.objects.all()
    serializer_class = SchoolFeesDataSerializer
    # permission_classes = [IsAuthenticated]
    

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter to only return the authenticated user's data
        return User.objects.filter(id=self.request.user.id)
    
  
# Student and teacher views
class StudentUserListView(ListAPIView):
    # permission_classes = [AllowAny]
    permission_classes = [IsAuthenticated]
    queryset = User.objects.filter(user_type='student')
    serializer_class = UserSerializer

class TeacherUserListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]
    # queryset = User.objects.filter(user_type='teacher')
    queryset = User.objects.filter(user_type__in=['teacher', 'admin', 'vpi', 'vpa', 'dean', 'it personel', 'business manager'])
    serializer_class = UserSerializer


class SuperParentsListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]
    queryset = User.objects.exclude(user_type='student')
    serializer_class = UserSerializer


# LinkStudents

from django.db.models import OuterRef, Subquery, Sum, Value, DecimalField, Count, Q, F, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.db.models import Prefetch

class MyLinkedStudentsView(ListAPIView):
    serializer_class = StudentAdmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type != 'student':
            qs = StudentAdmission.objects.filter(parent=user)
        else:
            qs = StudentAdmission.objects.filter(user=user)

        payment_total_fee_subquery = Payment.objects.filter(
            student=OuterRef('pk')  # Replace 'student' with your actual FK field name
        ).values('student').annotate(
            total_fee_sum=Sum('total_fee', output_field=DecimalField(max_digits=10, decimal_places=2))
        ).values('total_fee_sum')

        payment_amount_paid_subquery = Payment.objects.filter(
            student=OuterRef('pk')
        ).values('student').annotate(
            amount_paid_sum=Sum('amount_paid', output_field=DecimalField(max_digits=10, decimal_places=2))
        ).values('amount_paid_sum')

        qs = qs.annotate(
            total_fee=Coalesce(
                Subquery(payment_total_fee_subquery, output_field=DecimalField(max_digits=10, decimal_places=2)),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
            ),
            amount_paid=Coalesce(
                Subquery(payment_amount_paid_subquery, output_field=DecimalField(max_digits=10, decimal_places=2)),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
            ),
            total_present=Count('attendance_records', filter=Q(attendance_records__status='present')),
            total_absent=Count('attendance_records', filter=Q(attendance_records__status='absent')),
            total_late=Count('attendance_records', filter=Q(attendance_records__status='late')),
        ).annotate(
            balance_fee=ExpressionWrapper(
                F('total_fee') - F('amount_paid'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).select_related('user', 'parent', 'grade_class', 'division_assigned')

        # Add complaints prefetch
        qs = qs.prefetch_related(
            Prefetch('complaints', queryset=Complaint.objects.select_related('poster').order_by('-created_at'))
        )

        return qs
    

class LinkedStudentGradesView(ListAPIView):
    serializer_class = StudentAverageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        student_id = self.request.query_params.get('student_id')
        period_id = self.request.query_params.get('period_id')

        # Default empty queryset
        qs = StudentAverage.objects.none()

        # Fetch student first (regardless of who is asking)
        student_admission = get_object_or_404(StudentAdmission, pk=student_id)

        # Check if user is linked to the student (as parent)
        if user.user_type in ['parent', 'teacher', 'registry', 'business_manager', 'vpi', 'vpa', 'dean', 'it_personnel']:
            if student_admission.parent == user:
                qs = StudentAverage.objects.filter(student=student_admission, published=True)
            else:
                # Not linked — no access
                return StudentAverage.objects.none()

        elif user.user_type == 'student':
            # Student can only view their own grades
            if student_admission.user == user:
                qs = StudentAverage.objects.filter(student=student_admission)
            else:
                return StudentAverage.objects.none()

        else:
            # For admin roles
            qs = StudentAverage.objects.filter(student=student_admission)

        if period_id:
            qs = qs.filter(period_id=period_id)

        return qs.select_related('student', 'grade_class', 'period')




# //LinkStudents End
    


class GradeClassListView(viewsets.ModelViewSet):
    queryset = GradeClass.objects.all()
    serializer_class = GradeClassSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user
        user_type = getattr(user, "user_type", None)

        if user_type in ['admin', 'dean', 'vpa', 'vpi', 'business manager', 'registry']:
            # Return all grade classes
            queryset = GradeClass.objects.all()
        elif user_type == 'teacher':
            try:
                teacher = TeacherDataProcess.objects.get(username=user)
                queryset = teacher.grade_class.all()
            except TeacherDataProcess.DoesNotExist:
                queryset = GradeClass.objects.none()
        else:
            queryset = GradeClass.objects.none()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class GradeClassRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GradeClass.objects.all()
    serializer_class = GradeClassSerializer
    permission_classes = [IsAuthenticated]


class GradeClassCountView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        count = GradeClass.count()
        return Response({"count": count})


class GradeClassViewSet(ReadOnlyModelViewSet):  # ✅ USE ViewSet
    queryset = GradeClass.objects.all()
    serializer_class = GradeClassSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100  


class MyChildrenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.user_type != 'parent':
            return Response({'detail': 'Only parents can access this endpoint.'}, status=403)
        children = StudentAdmission.objects.filter(parent=request.user, status='Enrolled')
        serializer = StudentAdmissionSerializer(children, many=True)
        return Response(serializer.data)
    

class StudentAdmissionView(viewsets.ModelViewSet):
    queryset = StudentAdmission.objects.none()
    serializer_class = StudentAdmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        year_id = self.request.query_params.get("academic_year")

        full_access_roles = [
            'admin',
            'teacher',
            'registry',
            'business manager',
            'vpi',
            'vpa',
            'dean',
            'it personnel',
        ]

        qs = StudentAdmission.objects.all()

        # filter by academic year if passed
        if year_id:
            qs = qs.filter(academic_year_id=year_id)

        if user.user_type in full_access_roles:
            return qs
        elif user.user_type == 'parent':
            return qs.filter(parent=user)
        elif user.user_type == 'student':
            return qs.filter(user=user)
        return StudentAdmission.objects.none()

    def perform_create(self, serializer):
        # require academic_year when creating new admissions
        year_id = self.request.data.get("academic_year")
        if not year_id:
            raise ValueError("academic_year is required when creating a student admission")
        academic_year = AcademicYear.objects.get(id=year_id)
        serializer.save(academic_year=academic_year)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_students(request):
    grade_class_id = request.GET.get('grade_class')
    print(f"Grade Class ID received: {grade_class_id}")  # Debugging

    if grade_class_id:
        students = StudentAdmission.objects.filter(
            grade_class_id=grade_class_id, status='Enrolled'
        ).values('id', 'full_name')

        print(f"Filtered Students: {list(students)}")  # Debugging
        return JsonResponse(list(students), safe=False)

    return JsonResponse([], safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def count_by_semester(request):
    counts = StudentAdmission.count_admissions_per_semester()
    return Response(counts)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def count_by_gender(request):
    counts = StudentAdmission.count_by_gender()
    return Response(counts)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subject_count_by_student_division(request):
    try:
        # Get the logged-in student's admission info
        student_admission = StudentAdmission.objects.get(user=request.user)

        # Get the division
        division = student_admission.division_assigned

        # Count subjects assigned to this division
        subject_count = Subject.objects.filter(division_assigned=division).count()

        data = {
            "division_name": division.name,
            "subject_count": subject_count
        }

        serializer = SubjectCountByDivisionSerializer(data)
        return Response(serializer.data)

    except StudentAdmission.DoesNotExist:
        return Response({"error": "StudentAdmission record not found."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_admission_detail(request):
    try:
        student_admission = StudentAdmission.objects.get(user=request.user)
        serializer = StudentAdmissionDetailSerializer(student_admission)
        return Response(serializer.data)
    except StudentAdmission.DoesNotExist:
        return Response({"error": "StudentAdmission record not found."}, status=404)


class StudentAdmissionCountView(APIView):
    def get(self, request):
        # Get the count of student admissions per semester
        semester_count = StudentAdmission.count_admissions_per_semester()
        return Response(semester_count, status=status.HTTP_200_OK)


class StudentRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.filter(user_type='student')
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    # permission_classes = [IsAuthenticated]user_type


    




class ExpenditureViewSet(ModelViewSet):
    queryset = Expenditure.objects.all()
    serializer_class = ExpenditureSerializer



class TeacherDataViewSet(viewsets.ModelViewSet):
    queryset = TeacherDataProcess.objects.all()
    serializer_class = TeacherDataProcessSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["full_name"]
    permission_classes = [IsAuthenticated]



class LoanViewSet(ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer


class RegistrationView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [IsAuthenticated]  

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Mark user as online by updating last_seen
            user.last_seen = timezone.now()
            user.save(update_fields=['last_seen'])

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
                "profile_image": user.profile_image.url if user.profile_image else None,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CustomLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.last_seen = timezone.now()  # Set last_seen to the exact time of logout
        user.is_online = False  # Mark the user as offline
        user.save(update_fields=['last_seen', 'is_online'])
        return Response({"detail": "Logged out successfully and last_seen updated."})



class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        print("Status module is:", status)
        print("Received refresh request:", request.data)
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except Exception as e:
            print("Error during token refresh:", e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


        
        
class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user  # Access the authenticated user
        if user.is_authenticated:
            return Response({
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
                "profile_image": user.profile_image.url if user.profile_image else None,
            })
        return Response({"error": "Unauthorized"}, status=401)
    








class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "user_type": getattr(user, 'user_type', None),
            "profile_image": user.profile_image.url if user.profile_image else None,
            "is_active": user.is_active,  # this still means "is account enabled"
            "is_online": user.is_online,  # ✅ real-time online/offline status
            "last_seen": user.last_seen,  # optional: can help show "Last seen X mins ago"
        }
        return Response(user_data)

    def put(self, request):
        serializer = ProfileImageSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile image updated successfully.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class CountsView(APIView):
    """
    API view to fetch counts and aggregate data for admin users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # if user.user_type != 'admin':
        if user.user_type not in ['admin', 'registry', 'business manager','vpi', 'vpa', 'dean']:
            return Response({"detail": "Permission denied."}, status=403)

        total_students = User.objects.filter(user_type='student').count()
        total_teachers = User.objects.filter(user_type='teacher').count()
        total_schoolfee = Payment.objects.aggregate(total_schoolfee=models.Sum('amount_paid'))['total_schoolfee'] or 0
        total_salary = TeacherDataProcess.objects.aggregate(total_salary=models.Sum('salary'))['total_salary'] or 0
        expenditure = Expenditure.objects.aggregate(expenditure=models.Sum('amount'))['expenditure'] or 0

        counts_data = {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_schoolfee": total_schoolfee,
            "total_salary": total_salary,
            "expenditure": expenditure
        }

        return Response(counts_data)



class AllUsersViewSet(viewsets.ModelViewSet):
    """
    Viewset to fetch all users excluding the logged-in user.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Fetch all users excluding the logged-in user
        return User.objects.exclude(id=self.request.user.id)  
        
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user  # Get the logged-in user

        # Check if the user is an admin
        
        if user.user_type in ['admin', 'business manager', 'registry']:
            return Payment.objects.all()  # Admins can view all payments

        # For students, filter payments linked to them
        if user.user_type == 'student':
            student = StudentAdmission.objects.filter(user=user).first()  # Safely get student linked to the user
            if student:
                return Payment.objects.filter(student=student)  # Filter payments for the logged-in student

        return Payment.objects.none()  # Return empty queryset if not an admin or student


class StaffSalaryView(APIView):
    permission_classes = [IsAuthenticated]
    """
    API for creating and viewing staff salary records with balance calculation.
    """

    def get(self, request):
        """
        Retrieve all staff salary records.
        """
        salaries = StaffSalary.objects.all()
        serializer = StaffSalarySerializer(salaries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new staff salary record with balance calculation.
        """
        data = request.data
        base_salary = data.get("base_salary", 0.00)
        bonus = data.get("bonus", 0.00)
        deductions = data.get("deductions", 0.00)

        # Calculate balance_salary
        try:
            balance_salary = float(base_salary) + float(bonus) - float(deductions)
        except ValueError:
            return Response(
                {"error": "Invalid numeric values for base_salary, bonus, or deductions."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Include calculated balance_salary in the data
        salary_data = {
            "teacher": data.get("teacher"),
            "base_salary": base_salary,
            "bonus": bonus,
            "deductions": deductions,
            "balance_salary": balance_salary,
        }

        serializer = StaffSalarySerializer(data=salary_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



from rest_framework.permissions import BasePermission

class IsAdminRegistryBusiness(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type in ["admin", "registry", "business manager", "vpa"]



class UserDetailsPageView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRegistryBusiness]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("search", "").strip()
        if not query:
            return Response({"error": "Search query is required."}, status=400)

        user_results = []

        # Search Users by username containing query
        users = User.objects.filter(username__icontains=query)
        for user in users:
            user_data = UserSerializer(user, context={'request': request}).data
            user_data["full_name"] = user.get_full_name() or user.username

            if user.user_type == "teacher":
                teacher = TeacherDataProcess.objects.filter(username=user).first()
                if teacher:
                    user_data["teacher_data"] = TeacherDataProcessSerializer(teacher, context={'request': request}).data
                    payroll = Payroll.objects.filter(teacher=teacher).first()
                    if payroll:
                        user_data["payroll_data"] = PayrollSerializer(payroll, context={'request': request}).data

            elif user.user_type == "student":
                student = StudentAdmission.objects.filter(user=user).first()
                if student:
                    user_data["student_data"] = StudentAdmissionSerializer(student, context={'request': request}).data
                    payments = Payment.objects.filter(student=student)
                    user_data["payments"] = [
                        {
                            "semester": payment.semester,
                            "total_fee": str(payment.total_fee),
                            "amount_paid": str(payment.amount_paid),
                            "balance_fee": str(payment.balance_fee),
                            "date": payment.date.strftime("%Y-%m-%d") if payment.date else None,
                            "student_class": payment.student_class.name if payment.student_class else None,
                        }
                        for payment in payments
                    ]

            user_results.append(user_data)

        # Search SupportStaff by full_name containing query
        support_staff_matches = SupportStaff.objects.filter(full_name__icontains=query)
        for staff in support_staff_matches:
            staff_data = SupportStaffSerializer(staff, context={'request': request}).data
            staff_data["full_name"] = staff.full_name
            staff_data["is_supportstaff"] = True  # tag to identify in frontend

            # Get payroll records for this support staff by full_name
            payrolls = Payroll.objects.filter(support_staff_name=staff.full_name).order_by('-created_at')
            staff_data["payrolls"] = PayrollSerializer(payrolls, many=True, context={'request': request}).data

            user_results.append(staff_data)

        if not user_results:
            return Response({
                "message": f"No matching users or support staff found for '{query}'."
            })

        return Response({
            "users": user_results
        })




