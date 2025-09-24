from rest_framework import viewsets, permissions, status
from django.core.mail import EmailMultiAlternatives
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification
from datetime import date
from django.db.models import Sum
from decimal import Decimal
from rest_framework.response import Response

from teacherdata.models import TeacherDataProcess
from .serializers import PayrollSerializer, SalaryAdvanceSerializer
from django.core.mail import send_mail
from django.conf import settings
from .models import Payroll, SalaryAdvance
import base64
import os


class IsAdminOrBusinessManager(permissions.BasePermission):
    """
    Custom permission to allow access only to users with user_type
    'admin' or 'business_manager'.
    """

    def has_permission(self, request, view):
        user = request.user
        # Make sure user is authenticated
        if not user or not user.is_authenticated:
            return False

        # Check if user_type matches either 'admin' or 'business_manager'
        return user.user_type in ['admin', 'business manager', 'vpa']
    
# class PayrollViewSet(viewsets.ModelViewSet):
#     queryset = Payroll.objects.select_related('teacher').all()
#     serializer_class = PayrollSerializer
#     permission_classes = [IsAdminOrBusinessManager]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         payroll = serializer.save()

#         teacher = payroll.teacher  # Get the full User object

#         # if teacher and teacher.email:
#         if teacher and teacher.user and teacher.user.email:
#             logo_url = "https://www.janalwilliamsedufoundation.com/logoo.png"

#             text_message = (
#                 f"Hello {teacher.full_name},\n\n"
#                 f"Your payroll for {payroll.month} {payroll.year} has been processed.\n\n"
#                 f"Basic Salary: ${payroll.basic_salary:.2f}\n"
#                 f"Bonus: ${payroll.bonus:.2f}\n"
#                 f"Deductions: -${payroll.deductions:.2f}\n"
#                 f"Salary Advance: -${payroll.salary_advance:.2f}\n"
#                 f"Total Paid: ${payroll.total_paid:.2f}\n\n"
#                 f"Thank you,\n"
#                 f"Business Manager"
#             )

#             html_message = f"""
#             <html>
#               <body style="margin:0; padding:0; font-family: Arial, sans-serif;">
#                 <div style="background-color:#003366; color: white; padding: 15px 20px; display: flex; align-items: center;">
#                   {'<img src="' + logo_url + '" alt="School Logo" style="height:50px; margin-right:15px;" />' if logo_url else ''}
#                   <div style="line-height: 1;">
#                     <h1 style="margin: 0; font-size: 24px; font-weight: bold;">Jana Williams</h1>
#                     <span style="font-size: 16px;">Education Foundation</span>
#                   </div>
#                 </div>
#                 <div style="background-color:#fff9c4; color: #5a4d00; padding: 8px 20px; font-size:14px;">
#                   123 Main Street, Monrovia, Liberia | Phone: +231 777 123 456 | Email: info@jenewilliamsschool.edu.lr
#                 </div>
#                 <div style="background-color:#f5f5f5; color:#555555; padding: 20px;">
#                   <p>Hello <strong>{teacher.full_name}</strong>,</p>
#                   <p>Your payroll for <strong>{payroll.month} {payroll.year}</strong> has been processed. Please find the details below:</p>
#                   <table style="width: 100%; max-width: 400px; border-collapse: collapse; margin: 20px 0;">
#                     <tr style="background-color:#e0e0e0;">
#                       <th style="text-align:left; padding:8px;">Basic Salary</th>
#                       <td style="padding:8px;">${payroll.basic_salary:.2f}</td>
#                     </tr>
#                     <tr>
#                       <th style="text-align:left; padding:8px; background-color:#e0e0e0;">Bonus</th>
#                       <td style="padding:8px;">${payroll.bonus:.2f}</td>
#                     </tr>
#                     <tr>
#                       <th style="text-align:left; padding:8px; background-color:#e0e0e0;">Deductions</th>
#                       <td style="padding:8px;">-${payroll.deductions:.2f}</td>
#                     </tr>
#                     <tr>
#                       <th style="text-align:left; padding:8px; background-color:#e0e0e0;">Salary Advance</th>
#                       <td style="padding:8px;">-${payroll.salary_advance:.2f}</td>
#                     </tr>
#                     <tr>
#                       <th style="text-align:left; padding:8px; background-color:#e0e0e0;">Total Paid</th>
#                       <td style="padding:8px; font-weight:bold;">${payroll.total_paid:.2f}</td>
#                     </tr>
#                   </table>
#                   <p>Thank you,</p>
#                   <div style="background-color:#d32f2f; color: white; display: inline-block; padding: 8px 15px; border-radius: 5px; font-weight: bold;">
#                     Business Manager
#                   </div>
#                 </div>
#               </body>
#             </html>
#             """

#             email = EmailMultiAlternatives(
#                 subject="Salary Payment Processed",
#                 body=text_message,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[teacher.user.email],
#             )
#             email.attach_alternative(html_message, "text/html")

#             try:
#                 email.send(fail_silently=False)
#             except Exception as e:
#                 print("❌ Email sending error:", e)

#             # Create notification
#             Notification.objects.create(
#                 user=teacher.user,
#                 message=f"Your payroll for {payroll.month} {payroll.year} has been processed. Total Paid: ${payroll.total_paid:.2f}",
#                 type='general'
#             )

#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class PayrollViewSet(viewsets.ModelViewSet):
    queryset = Payroll.objects.select_related('teacher').all()
    serializer_class = PayrollSerializer
    permission_classes = [IsAdminOrBusinessManager]
    # permission_classes = [permissions.IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payroll = serializer.save()

        if payroll.teacher and hasattr(payroll.teacher, 'username'):
            user = payroll.teacher.username

            # ✅ Use a publicly accessible image URL
            logo_url = "https://www.janalwilliamsedufoundation.com/logoo.png"  # ← Replace with your actual logo URL

            text_message = (
                f"Hello {payroll.teacher.full_name},\n\n"
                f"Your payroll for {payroll.month} {payroll.year} has been processed.\n\n"
                f"Basic Salary: ${payroll.basic_salary:.2f}\n"
                f"Bonus: ${payroll.bonus:.2f}\n"
                f"Deductions: -${payroll.deductions:.2f}\n"
                f"Total Paid: ${payroll.total_paid:.2f}\n\n"
                f"Thank you,\n"
                f"Business Manager"
            )

            html_message = f"""
            <html>
              <body style="margin:0; padding:0; font-family: Arial, sans-serif;">
                <div style="background-color:#003366; color: white; padding: 15px 20px; display: flex; align-items: center;">
  <!-- Image on the left -->
  {'<img src="' + logo_url + '" alt="School Logo" style="height:50px; margin-right:15px;" />' if logo_url else ''}
  
  <!-- Text block without flex -->
  <div style="line-height: 1;">
    <h1 style="margin: 0; font-size: 24px; font-weight: bold;">Jana Williams</h1>
    <span style="font-size: 16px;">Education Foundation</span>
  </div>
</div>
                <div style="background-color:#fff9c4; color: #5a4d00; padding: 8px 20px; font-size:14px;">
                  123 Main Street, Monrovia, Liberia | Phone: +231 777 123 456 | Email: info@jenewilliamsschool.edu.lr
                </div>
                <div style="background-color:#f5f5f5; color:#555555; padding: 20px;">
                  <p>Hello <strong>{payroll.teacher.full_name}</strong>,</p>
                  <p>Your payroll for <strong>{payroll.month} {payroll.year}</strong> has been processed. Please find the details below:</p>
                  <table style="width: 100%; max-width: 400px; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color:#e0e0e0;">
                      <th style="text-align:left; padding:8px;">Basic Salary</th>
                      <td style="padding:8px;">${payroll.basic_salary:.2f}</td>
                    </tr>
                    <tr>
                      <th style="text-align:left; padding:8px; background-color:#e0e0e0;">Bonus</th>
                      <td style="padding:8px;">${payroll.bonus:.2f}</td>
                    </tr>
                    <tr>
                      <th style="text-align:left; padding:8px; background-color:#e0e0e0;">Deductions</th>
                      <td style="padding:8px;">-${payroll.deductions:.2f}</td>
                    </tr>
                     <tr>
                      <th style="text-align:left; padding:8px; background-color:#e0e0e0;">Salary Advance</th>
                      <td style="padding:8px;">-${payroll.salary_advance:.2f}</td>
                    </tr>
                    <tr>
                      <th style="text-align:left; padding:8px; background-color:#e0e0e0;">Total Paid</th>
                      <td style="padding:8px; font-weight:bold;">${payroll.total_paid:.2f}</td>
                    </tr>
                  </table>
                  <p>Thank you,</p>
                  <div style="background-color:#d32f2f; color: white; display: inline-block; padding: 8px 15px; border-radius: 5px; font-weight: bold;">
                    Business Manager
                  </div>
                </div>
              </body>
            </html>
            """

            email = EmailMultiAlternatives(
                subject="Salary Payment Processed",
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")

            try:
                email.send(fail_silently=False)
            except Exception as e:
                print("❌ Email sending error:", e)

            Notification.objects.create(
                user=user,
                message=f"Your payroll for {payroll.month} {payroll.year} has been processed. Total Paid: ${payroll.total_paid:.2f}",
                type='general'
            )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



from rest_framework.decorators import api_view
@api_view(['GET'])
def get_teacher_salary(request, teacher_id):
    try:
        teacher = TeacherDataProcess.objects.get(id=teacher_id)
        return Response({'salary': teacher.salary})
    except TeacherDataProcess.DoesNotExist:
        return Response({'error': 'Teacher not found'}, status=404)
    


class SalaryAdvanceViewSet(viewsets.ModelViewSet):
    queryset = SalaryAdvance.objects.select_related('teacher', 'support_staff').all()
    serializer_class = SalaryAdvanceSerializer
    permission_classes = [permissions.IsAdminUser]  # Change to IsAuthenticated if needed

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save()


@api_view(['GET'])
def current_month_salary_advance(request):
    teacher_id = request.query_params.get('teacher_id')
    support_staff_name = request.query_params.get('support_staff_name')

    current_month = date.today().strftime('%B')
    current_year = date.today().year

    filters = {
        'month': current_month,
        'year': current_year,
    }

    if teacher_id:
        filters['teacher_id'] = teacher_id
    elif support_staff_name:
        filters['support_staff__full_name'] = support_staff_name
    else:
        return Response({'total_advance': 0})

    total = SalaryAdvance.objects.filter(**filters).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    return Response({'total_advance': float(total)})








