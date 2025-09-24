from django.db import models
from academics.models import Division, GradeClass, Subject
from reportcard.models import Period
from users.models import User



class TeacherDataProcess(models.Model):
    username = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': ['teacher', 'admin', 'vpi', 'vpa', 'dean', 'it personel', 'business manager']}
       
    )
    full_name = models.CharField(max_length=80)
    qualification = models.CharField(max_length=50)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject, blank=True)  # <-- optional now
    grade_class = models.ManyToManyField(GradeClass, blank=True)  # <-- already optional
    # subjects = models.ManyToManyField(Subject)
    # grade_class = models.ManyToManyField(GradeClass, blank=True)  
    dependent_student = models.CharField(max_length=50)
    contact = models.CharField(max_length=20)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    date_add = models.DateField()

    def __str__(self):
        return f"{self.full_name}, {self.division} - {self.salary} on {self.date_add}"
    

class TeacherLessonPlan(models.Model):
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'teacher'},
        related_name='lesson_plans'
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)
    objectives = models.TextField()
    content = models.TextField()
    teaching_method = models.TextField()
    assessment = models.TextField()
    week = models.CharField(max_length=20)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('teacher', 'subject', 'grade_class', 'week')
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.teacher} - {self.subject.name} ({self.grade_class.name}) - {self.period.name} - Week {self.week}"



# class TeacherDataProcess(models.Model):
#     user = models.OneToOneField(
#         User, 
#         on_delete=models.CASCADE, 
#         limit_choices_to={'user_type': ['teacher', 'admin', 'vpi', 'vpa', 'dean', 'it personel', 'business manager']}
       
#     )
#     full_name = models.CharField(max_length=80)
#     qualification = models.CharField(max_length=50)
#     division = models.ForeignKey(Division, on_delete=models.CASCADE)
#     subjects = models.ManyToManyField(Subject, blank=True)  # <-- optional now
#     grade_class = models.ManyToManyField(GradeClass, blank=True)  # <-- already optional
#     # subjects = models.ManyToManyField(Subject)
#     # grade_class = models.ManyToManyField(GradeClass, blank=True)  
#     dependent_student = models.CharField(max_length=50)
#     contact = models.CharField(max_length=20)
#     salary = models.DecimalField(max_digits=10, decimal_places=2)
#     date_add = models.DateField()

#     def __str__(self):
#         return f"{self.full_name}, {self.division} - {self.salary} on {self.date_add}"
    

# class TeacherLessonPlan(models.Model):
#     teacher = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         limit_choices_to={'user_type': 'teacher'},
#         related_name='lesson_plans'
#     )
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
#     grade_class = models.ForeignKey(GradeClass, on_delete=models.CASCADE)
#     period = models.ForeignKey(Period, on_delete=models.CASCADE)
#     topic = models.CharField(max_length=100)
#     objectives = models.TextField()
#     content = models.TextField()
#     teaching_method = models.TextField()
#     assessment = models.TextField()
#     week = models.CharField(max_length=20)
#     date_created = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('teacher', 'subject', 'grade_class', 'week')
#         ordering = ['-date_created']

#     def __str__(self):
#         return f"{self.teacher} - {self.subject.name} ({self.grade_class.name}) - {self.period.name} - Week {self.week}"





class SupportStaff(models.Model):
    full_name = models.CharField(max_length=80)
    department = models.CharField(max_length=100)
    dependent_student = models.CharField(max_length=50)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    contact = models.CharField(max_length=20)
    date_add = models.DateField()
    image = models.ImageField(upload_to='supportstaff_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.full_name}, {self.department} - {self.salary} on {self.date_add}"

