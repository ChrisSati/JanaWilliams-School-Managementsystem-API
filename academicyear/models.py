from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q

class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True)  # e.g. "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)  # only one active at a time

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate all other active academic years before saving
            AcademicYear.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date.")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=Q(is_active=True),
                name="only_one_active_academic_year"
            )
        ]

    def __str__(self):
        return self.name
