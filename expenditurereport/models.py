from django.db import models
from academics.models import GradeClass, StudentAdmission
from decimal import Decimal
from loan.models import Loan
from payroll.models import SalaryAdvance
from teacherdata.models import SupportStaff, TeacherDataProcess
from scoolfeedata.models import Payment, SchoolFeesData
from users.models import User
from django.db.models import Sum
from datetime import datetime
from calendar import monthrange


# Month choices
MONTH_CHOICES = [ 
    ('January', 'January'),
    ('February', 'February'),
    ('March', 'March'),
    ('April', 'April'),
    ('May', 'May'),
    ('June', 'June'),
    ('July', 'July'),
    ('August', 'August'),
    ('September', 'September'),
    ('October', 'October'),
    ('November', 'November'),
    ('December', 'December'),
]


# 1. Expenditure Model
class Expenditure(models.Model):
    CATEGORY_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('utilities', 'Utilities'),
        ('supplies', 'Supplies'),
        ('events', 'Events'),
        ('transportation', 'Transportation'),
        ('miscellaneous', 'Miscellaneous'),
    ]

    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.title} - ${self.amount}"



# Done
SEMESTER_CHOICES = [
    ('First', 'First'),
    ('Second', 'Second'),
]

class FeesPerGradeClass(models.Model):
    grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    year = models.IntegerField()

    class Meta:
        unique_together = ('grade_class', 'semester', 'year')

    def __str__(self):
        return f"{self.grade_class.name} - {self.semester} Semester {self.year}"

    @property
    def fees_expected(self):
        try:
            school_fee = SchoolFeesData.objects.get(grade_class=self.grade_class)
            semester_fee = school_fee.yearly_school_fee / Decimal("2")
        except SchoolFeesData.DoesNotExist:
            return Decimal("0.00")

        # Get unique student IDs who paid in this grade_class and semester/year
        student_ids = Payment.objects.filter(
            student_class=self.grade_class,
            semester=self.semester,
            date__year=self.year
        ).values_list('student_id', flat=True).distinct()

        num_students = len(student_ids)

        expected_total = semester_fee * num_students
        return expected_total.quantize(Decimal("0.01"))

    @property
    def fees_collected(self):
        total_paid = Payment.objects.filter(
            student_class=self.grade_class,
            semester=self.semester,
            date__year=self.year
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal("0.00")

        return Decimal(total_paid).quantize(Decimal("0.01"))

    @property
    def balance(self):
        return self.fees_expected - self.fees_collected
    

class Fee(models.Model):
    FEE_TYPE_CHOICES = [
        ('graduation', 'Graduation Fee'),
        ('entrance', 'Entrance Fee'),
        ('project', 'Project Fee'),
        ('activities', 'Activities Fee'),
        ('wacce', 'WACCE Fee'),
        ('extra_class', 'Extra Class Fee'),
    ]

    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE, null=True, blank=True)
    entrance_student_name = models.CharField(max_length=100, blank=True)
    grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPE_CHOICES)

    fee_charge = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total fee to be paid")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount paid so far")
    balance = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fee Charge - Amount Paid", blank=True)

    date_paid = models.DateField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # ✅ Correct calculation: balance = fee_charge - amount
        if self.fee_charge is not None and self.amount is not None:
            self.balance = self.fee_charge - self.amount
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.student.full_name if self.student else self.entrance_student_name
        return f"{name} - {self.get_fee_type_display()} - Paid: ${self.amount} / Charge: ${self.fee_charge} / Balance: ${self.balance}"



    
MONTH_CHOICES = [ 
    ('January', 'January'),
    ('February', 'February'),
    ('March', 'March'),
    ('April', 'April'),
    ('May', 'May'),
    ('June', 'June'),
    ('July', 'July'),
    ('August', 'August'),
    ('September', 'September'),
    ('October', 'October'),
    ('November', 'November'),
    ('December', 'December'),
]


class MonthlyFinancialRecord(models.Model):
    month = models.CharField(max_length=20, choices=MONTH_CHOICES)
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    donation_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('month', 'year')

    def __str__(self):
        return f"{self.month} {self.year} Financial Record"

    def _get_date_range(self):
        try:
            month_num = datetime.strptime(self.month, '%B').month
        except ValueError:
            month_num = int(self.month)
        start = datetime(self.year, month_num, 1)
        end = datetime(self.year, month_num, monthrange(self.year, month_num)[1], 23, 59, 59)
        return start, end

    @property
    def school_fees_total(self):
        start, end = self._get_date_range()
        total = Payment.objects.filter(date__range=(start, end)).aggregate(total=Sum('amount_paid'))['total']
        return Decimal(total or 0).quantize(Decimal('0.01'))

    @property
    def salary_advance_total(self):
        start, end = self._get_date_range()
        total = SalaryAdvance.objects.filter(created_at__range=(start, end)).aggregate(total=Sum('amount'))['total']
        return Decimal(total or 0).quantize(Decimal('0.01'))

    @property
    def staff_loan_total(self):
        start, end = self._get_date_range()
        total = Loan.objects.filter(date_taken__range=(start, end)).aggregate(total=Sum('amount'))['total']
        return Decimal(total or 0).quantize(Decimal('0.01'))

    @property
    def staff_salary_total(self):
        start, end = self._get_date_range()

        teacher_total = TeacherDataProcess.objects.filter(
            date_add__range=(start, end)
        ).aggregate(total=Sum('salary'))['total'] or 0

        staff_total = SupportStaff.objects.filter(
            date_add__range=(start, end)
        ).aggregate(total=Sum('salary'))['total'] or 0

        total = teacher_total + staff_total
        return Decimal(total).quantize(Decimal('0.01'))

    @property
    def other_expenditures_total(self):
        start, end = self._get_date_range()
        total = Expenditure.objects.filter(date__range=(start, end)).aggregate(total=Sum('amount'))['total']
        return Decimal(total or 0).quantize(Decimal('0.01'))

    @property
    def total_income(self):
        return self.school_fees_total + self.donation_income

    @property
    def total_expenses(self):
        return (
            self.staff_salary_total +
            self.staff_loan_total +
            self.other_expenditures_total
        )

    @property
    def net_balance(self):
        return self.total_income - self.total_expenses


# 5. Financial Line Items (Optional: Auditing)
class FinancialLineItem(models.Model):
    financial_record = models.ForeignKey(MonthlyFinancialRecord, on_delete=models.CASCADE, related_name='line_items')
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=[('income', 'Income'), ('expense', 'Expense')])
    date = models.DateField()

    def __str__(self):
        return f"{self.title} - {self.type} - ${self.amount}"

