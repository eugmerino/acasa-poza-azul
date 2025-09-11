from django import forms
from .models import Fee, Range

class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ['short_description', 'approval_date', 'isActive']
        widgets = {
            'approval_date': forms.DateInput(attrs={'type': 'date'}),
        }

class RangeForm(forms.ModelForm):
    class Meta:
        model = Range
        fields = ['min_meter', 'max_meter', 'fixed_amount', 'amount_meter']