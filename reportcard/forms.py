from django import forms
from .models import GradeDistribution, StudentAdmission

class GradeDistributionForm(forms.ModelForm):
    class Meta:
        model = GradeDistribution
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        grade_class = kwargs.pop("grade_class", None)
        super().__init__(*args, **kwargs)

        if grade_class:
            self.fields["student"].queryset = StudentAdmission.objects.filter(grade_class=grade_class, status="Enrolled")
        else:
            self.fields["student"].queryset = StudentAdmission.objects.filter(status="Enrolled")


