from django.db import models
import uuid
from academics.models import StudentAdmission

class SchoolFeePayment(models.Model):
    SEMESTER_CHOICES = [
        ('1st Semester', 'First Semester'),
        ('2nd Semester', 'Second Semester'),
    ]

    SERVICES_CHOICES = [
        ('School Fee', 'School Fee'),
        ('Activities Fee', 'Activities Fee'),
        ('Wassce Fee', 'Wassce Fee'),
        ('Other  Fee', 'Other Fee'),
   ]
    
    # Foreign Key to Student model
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE)
    student_class = models.CharField(max_length=100)
    # Payer information
    payer_name = models.CharField(max_length=255)
    payer_contact = models.CharField(max_length=255)
    receipt_number = models.UUIDField(default=uuid.uuid4, editable=False)  # No unique=True
    date = models.DateField()
    
    # Semester and fee details
    semester = models.CharField(choices=SEMESTER_CHOICES, max_length=20)
    services = models.CharField(choices=SERVICES_CHOICES, max_length=20)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)



    @property
    def balance(self):
        return (self.amount_due or 0) - (self.amount_paid or 0)

    def __str__(self):
        return f"Payment for {self.student.full_name}, Receipt #{self.receipt_number}"


    