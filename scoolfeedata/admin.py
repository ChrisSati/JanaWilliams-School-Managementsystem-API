from django.contrib import admin

from receiptrecord.models import SchoolFeePayment
from scoolfeedata.models import  Payment,  SchoolFeesData



@admin.register(SchoolFeesData)
class SchoolFeesDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'grade_class', 'yearly_school_fee')
    list_filter = ['grade_class']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'semester', 'installment',  'student', 'student_class',  'total_fee', 'payer_name', 'amount_paid', 'date', 'balance_fee')
    list_filter = ['student']



@admin.register(SchoolFeePayment)
class SchoolFeePaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'student', 'semester', 'services', 'student_class', 'amount_due', 'amount_paid', 'balance', 'date')
    list_filter = ('semester', 'services', 'date')
    search_fields = ('receipt_number', 'student__full_name', 'payer_name')
    readonly_fields = ('balance',)
    
    def balance(self, obj):
        return obj.balance
       
 
# @admin.register(SchoolFeePayment)
# class SchoolFeePaymentAdmin(admin.ModelAdmin):
#     list_display = ['student', 'payer_name', 'receipt_number',  'semester', 'amount_due', 'amount_paid', 'balance', 'date']
#     search_fields = ['student__full_name', 'payer_name', 'receipt_number']
#     list_filter = ['semester', 'student__grade_class']
    
#     def balance(self, obj):
#         return obj.balance
#     balance.admin_order_field = 'amount_due'  # allows sorting by balance in admin


