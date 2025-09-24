from django.db import models
from users.models import User
from teacherdata.models import  SupportStaff, TeacherDataProcess
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
from datetime import date


class Payroll(models.Model):
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

    teacher = models.ForeignKey(
        TeacherDataProcess,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='payrolls'
    )
    support_staff_name = models.CharField(max_length=255, null=True, blank=True)

 

    month = models.CharField(max_length=20, choices=MONTH_CHOICES)
    year = models.IntegerField(default=date.today().year)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    salary_advance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if not self.teacher and not self.support_staff_name:
            raise ValidationError("Either teacher or support staff name must be set.")
        if self.teacher and self.support_staff_name:
            raise ValidationError("Only one of teacher or support staff name can be set.")

    def save(self, *args, **kwargs):
        if self.teacher:
            self.basic_salary = self.teacher.salary

        # Determine filters to query SalaryAdvance
        filters = {
            'month': self.month,
            'year': self.year,
        }

        if self.teacher:
            filters['teacher'] = self.teacher
        elif self.support_staff_name:
            try:
                staff = SupportStaff.objects.get(full_name=self.support_staff_name)
                filters['support_staff'] = staff
            except SupportStaff.DoesNotExist:
                staff = None
                filters.pop('support_staff', None)

        # Import inside method to avoid circular import issues
        from .models import SalaryAdvance

        salary_advance_total = SalaryAdvance.objects.filter(**filters).aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')

        self.salary_advance = salary_advance_total

        basic_salary = Decimal(self.basic_salary or 0)
        bonus = Decimal(self.bonus or 0)
        deductions = Decimal(self.deductions or 0)
        salary_advance = Decimal(self.salary_advance or 0)

        # Deduct salary advance from total_paid, not from basic_salary
        self.total_paid = basic_salary + bonus - deductions - salary_advance
        if self.total_paid < 0:
            self.total_paid = Decimal('0.00')

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.teacher:
            return f"{self.teacher.full_name} - {self.month} {self.year}"
        return f"{self.support_staff_name} - {self.month} {self.year}"


class SalaryAdvance(models.Model):
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

    teacher = models.ForeignKey(
        TeacherDataProcess,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='salary_advances'
    )
    support_staff = models.ForeignKey(
        SupportStaff,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='salary_advances'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    month = models.CharField(max_length=20, choices=MONTH_CHOICES, blank=True)
    year = models.IntegerField(null=True, blank=True)
    reason = models.TextField(blank=True, null=True)

    def clean(self):
        if not self.teacher and not self.support_staff:
            raise ValidationError('Either teacher or support_staff must be set.')
        if self.teacher and self.support_staff:
            raise ValidationError('Only one of teacher or support_staff can be set.')

    def save(self, *args, **kwargs):
        if not self.month and self.created_at:
            month_names = [month for month, _ in self.MONTH_CHOICES]
            self.month = month_names[self.created_at.month - 1]
        if not self.year and self.created_at:
            self.year = self.created_at.year
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.teacher.full_name if self.teacher else self.support_staff.full_name if self.support_staff else "N/A"
        return f"Advance for {name} - {self.amount} ({self.month} {self.year})"



MONTH_CHOICE = [
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

def get_current_year():
    return date.today().year

