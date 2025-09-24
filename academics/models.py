from django.db import models
from users.models import User
from academicyear.models import AcademicYear 



class Division(models.Model):
    name = models.CharField(max_length=70, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

  
    def __str__(self):
        return f"{self.name}"
    

class GradeClass(models.Model):
    name = models.CharField(max_length=100)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.name}"
    
    @classmethod
    def count(GradeClass):
        """Returns the total number of GradeClass instances."""
        return GradeClass.objects.count()
    



    

    
# Subject Model
class Subject(models.Model):
    name = models.CharField(max_length=100)
    division_assigned = models.ForeignKey(Division, on_delete=models.CASCADE)

    

    def __str__(self):
        return self.name
    
    @staticmethod
    def total_subject_count():
        return Subject.objects.count()
    
    
    
class StudentAdmission(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)  # NEW
    user = models.ForeignKey(User, related_name='admissions', on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'})
    parent = models.ForeignKey(
        User,
        related_name='linked_students',
        on_delete=models.CASCADE,
        limit_choices_to=~models.Q(user_type='student'),
        null=True,
        blank=True,
        help_text="The parent or guardian linked to this student"
    )
    full_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, choices=[('Male', 'Male'), ('Female', 'Female')])
    county_of_origin = models.CharField(max_length=100)
    previous_class = models.CharField(max_length=20)
    grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE)
    division_assigned =  models.ForeignKey(Division, on_delete=models.CASCADE)
    major_subject = models.CharField(max_length=50)
    previous_school = models.CharField(max_length=100)
    hobit = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    address = models.TextField()
    mother_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    health_status = models.CharField(max_length=100)
    parent_contact = models.CharField(max_length=15)
    enrollment_date = models.DateField()
    semester_status = models.CharField(max_length=50, choices=[('First', 'First'), ('Second', 'Second')])
   
    student_status = models.CharField(max_length=50, choices=[('Regular', 'Regular'), ('Dependent', 'Dependent'), ('Scholarship', 'Scholarship')])

    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Enrolled', 'Enrolled'), ('Graduated', 'Graduated'), ('Dropped', 'Dropped')])
    nationality = models.CharField(max_length=100)


    def __str__(self):
        return f"{self.full_name}"
    @staticmethod
    def count_admissions_per_semester():
        return {
            'first_semester': StudentAdmission.objects.filter(semester_status='First').count(),
            'second_semester': StudentAdmission.objects.filter(semester_status='Second').count(),
        }

    @staticmethod
    def count_by_gender():
        return {
            'male': StudentAdmission.objects.filter(gender='Male').count(),
            'female': StudentAdmission.objects.filter(gender='Female').count(),
        }
    

    

# Assignment Model
class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    assignment_subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="assignments")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignments")

    def __str__(self):
        return self.title


    



    



 