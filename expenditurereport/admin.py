from django.contrib import admin
from .models import (
    Expenditure,
    FeesPerGradeClass,
    Fee,
    MonthlyFinancialRecord,
    FinancialLineItem
)


@admin.register(Expenditure)
class ExpenditureAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'category', 'date', 'recorded_by')
    list_filter = ('category', 'date')
    search_fields = ('title', 'description')




@admin.register(FeesPerGradeClass)
class FeesPerGradeClassAdmin(admin.ModelAdmin):
    list_display = ('grade_class', 'semester', 'year', 'fees_expected', 'fees_collected', 'balance')
    list_filter = ('grade_class', 'semester', 'year')


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'entrance_student_name', 'grade_class', 'fee_type', 'fee_charge', 'amount', 'balance', 'date_paid')
    list_filter = ('fee_type', 'date_paid')
    search_fields = ('student__full_name',)


@admin.register(MonthlyFinancialRecord)
class MonthlyFinancialRecordAdmin(admin.ModelAdmin):
    list_display = ('month', 'year', 'total_income', 'total_expenses', 'net_balance', 'created_by', 'created_at')
    list_filter = ('month', 'year', 'created_by')
    search_fields = ('month',)


@admin.register(FinancialLineItem)
class FinancialLineItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'amount', 'date', 'financial_record')
    list_filter = ('type', 'date')
    search_fields = ('title',)
