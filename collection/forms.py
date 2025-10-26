from django import forms
from .models import Fee, Range, Reading
from django.core.exceptions import ValidationError

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

    def clean_receipt_number(self):
        """Valida que el número de recibo no esté duplicado."""
        receipt_number = self.cleaned_data.get('receipt_number')
        if receipt_number and Reading.objects.filter(receipt_number=receipt_number).exists():
            raise ValidationError('Ya existe una lectura con este número de recibo.')
        return receipt_number

    def clean_meter_reading(self):
        """Valida que la lectura del medidor sea positiva."""
        meter_reading = self.cleaned_data.get('meter_reading')
        if meter_reading is not None and meter_reading < 0:
            raise ValidationError('La lectura del medidor no puede ser negativa.')
        return meter_reading

    def clean(self):
        """Valida que la lectura actual sea mayor o igual a la lectura anterior."""
        cleaned_data = super().clean()
        meter_reading = cleaned_data.get('meter_reading')
        previous_reading = getattr(self.instance, 'previous_reading', None)

        if previous_reading is not None and meter_reading is not None:
            if meter_reading < previous_reading:
                self.add_error(
                    'meter_reading',
                    f'La lectura actual no puede ser menor a la lectura anterior.'
                )

        return cleaned_data