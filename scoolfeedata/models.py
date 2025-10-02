from django.db import models
from users.models import User
from academics.models import  GradeClass
from django.db.models import  Sum
from academics.models import StudentAdmission




class SchoolFeesData(models.Model):
    grade_class =  models.ForeignKey(GradeClass, on_delete=models.SET_NULL, null=True, related_name='fees')
    yearly_school_fee = models.DecimalField(max_digits=10, decimal_places=2)
  
    def __str__(self):
        return f"{self.grade_class} - {self.yearly_school_fee}"


class Payment(models.Model): 
     
    INSTALLMENT_CHOICES = [
        ('1st Installment', '1st Installment'),
        ('2nd Installment', '2nd Installment'),
        ('3rd Installment', '3rd Installment'),
    ]    
    
    installment = models.CharField(max_length=50, choices=INSTALLMENT_CHOICES, default='1st Installment')
    semester = models.CharField(max_length=50, choices=[('First', 'First'), ('Second', 'Second')])
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE)
    student_class =  models.ForeignKey(GradeClass, on_delete=models.SET_NULL, null=True, related_name='student_class')
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payer_name = models.CharField(max_length=100)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date = models.DateField(auto_now_add=True)
   
    balance_fee = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

   
    
    def save(self, *args, **kwargs):
       
        self.balance_fee = self.total_fee - self.amount_paid
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment of {self.total_fee}, {self.semester}, {self.installment}, {self.amount_paid} for {self.student}"
    



