from django.contrib import admin
from .models import Payroll, SalaryAdvance

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = (
        'get_staff_name', 'month', 'year', 'basic_salary', 
        'bonus', 'deductions', 'total_paid', 'is_paid', 'salary_advance', 'created_at'
    )
    list_filter = ('month', 'year', 'is_paid')
    search_fields = ('teacher__full_name', 'support_staff_name')
    ordering = ('-created_at',)

    def get_staff_name(self, obj):
        return obj.teacher.full_name if obj.teacher else obj.support_staff_name
    get_staff_name.short_description = 'Staff Name'



@admin.register(SalaryAdvance)
class SalaryAdvanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_teacher_name', 'get_support_staff_name', 'month', 'year', 'amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('teacher__full_name', 'support_staff_name')

    def get_teacher_name(self, obj):
        return obj.teacher.full_name if obj.teacher else '-'
    get_teacher_name.short_description = 'Teacher'

    def get_support_staff_name(self, obj):
        return obj.support_staff_name if obj.support_staff_name else '-'
    get_support_staff_name.short_description = 'Support Staff'


