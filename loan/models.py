from django.db import models

class Loan(models.Model):
    full_name = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_taken = models.DateField()
    date_due = models.DateField()

    def __str__(self):
        return f"Loan for {self.full_name}: {self.amount} taken on {self.date_taken}, due by {self.date_due}"

