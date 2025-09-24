from django.contrib import admin
from .models import StaffSalary





@admin.register(StaffSalary)
class StaffSalaryAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'base_salary', 'bonus', 'deductions', 'balance_salary', 'paid_on')
    search_fields = ('teacher__user__username',)
    list_filter = ('paid_on',)
