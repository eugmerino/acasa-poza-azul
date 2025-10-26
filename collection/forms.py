from django import forms
from .models import Fee, Range, Reading

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


class ReadingForm(forms.ModelForm):
    class Meta:
        model = Reading
        exclude = ['date_reading', 'fee', 'isPaid', 'previous_reading', 'penalty_fee', 'connection', 'late_payment'] 

        widgets = {
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° de recibo'
            }),
            'meter_reading': forms.NumberInput(attrs={
                'id': 'lectura-actual',
                'class': 'form-control',
                'placeholder': 'Lectura actual (m³)',
            }),
        }

        labels = {
            'receipt_number': 'N° de recibo',
            'meter_reading': 'Lectura del medidor (m³)',
        }