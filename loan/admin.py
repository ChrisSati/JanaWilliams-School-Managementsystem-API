from django.contrib import admin

from loan.models import Loan

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'description', 'amount', 'date_taken', 'date_due')
    search_fields = ('description', 'amount')
