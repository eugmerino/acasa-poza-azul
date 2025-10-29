from django import forms
from .models import Repair
from django.core.exceptions import ValidationError


class ReportForm(forms.ModelForm):
    class Meta:
        model = Repair
        fields = ['community', 'report_title', 'report_description', 'report_photo']
        widgets = {
            'community': forms.Select(attrs={'class': 'form-select'}),
            'report_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del reporte'}),
            'report_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción de la falla o reporte'}),
            'report_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'community': 'Comunidad',
            'report_title': 'Título del reporte',
            'report_description': 'Descripción del reporte',
            'report_photo': 'Foto del reporte',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["community"].empty_label = "Seleccione una comunidad..."

        
class RepairForm(forms.ModelForm):
    class Meta:
        model = Repair
        fields = ['repair_date', 'repair_description', 'repair_photo']
        widgets = {
            'repair_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'placeholder': 'Seleccione la fecha de reparación'
                }
            ),
            'repair_description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Descripción de la reparación'
                }
            ),
            'repair_photo': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control'
                }
            ),
        }
        labels = {
            'repair_date': 'Fecha de reparación',
            'repair_description': 'Descripción de la reparación',
            'repair_photo': 'Foto de la reparación',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['repair_date'].required = True
        self.fields['repair_description'].required = True
        self.fields['repair_photo'].required = True


class RepairPayForm(forms.ModelForm):
    class Meta:
        model = Repair
        fields = ['payment_amount', 'payment_date']
        widgets = {
            'payment_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ingrese el monto del pago'
                }
            ),
            'payment_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'placeholder': 'Seleccione la fecha de pago'
                }
            )
        }
        labels = {
            'payment_amount': 'Monto del pago',
            'payment_date': 'Fecha de pago',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_amount'].required = True
        self.fields['payment_date'].required = True

    def clean_payment_amount(self):
        """Evita valores negativos o cero en el monto del pago."""
        amount = self.cleaned_data.get('payment_amount')
        if amount is not None and amount <= 0:
            raise ValidationError('El monto del pago debe ser mayor que 0.')
        return amount