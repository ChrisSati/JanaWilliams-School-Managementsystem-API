from django.contrib import admin

from expenditure.models import Expenditure

@admin.register(Expenditure)
class ExpenditureAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date')
    search_fields = ('description', 'amount')
