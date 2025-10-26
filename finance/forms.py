# finance/forms.py
from django import forms
from .models import Transaction
from django.utils import timezone

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['project', 'concept', 'type', 'amount', 'date']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'concept': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Concepto de la transacción', 'required': True}),
            'type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'required': True}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
        }
        labels = {
            'project': 'Proyecto',
            'concept': 'Concepto',
            'type': 'Tipo',
            'amount': 'Monto',
            'date': 'Fecha',
        }

    # Validar monto
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor a 0.")
        return amount

    # Validar fecha (solo mes actual)
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if not date:
            raise forms.ValidationError("La fecha es obligatoria.")
        today = timezone.localdate()
        first_day = today.replace(day=1)
        last_day = (first_day + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)

        if date < first_day or date > last_day:
            raise forms.ValidationError("Solo se permiten fechas dentro del mes actual.")
        return date

    # Validar proyecto
    def clean_project(self):
        project = self.cleaned_data.get('project')
        if not project:
            raise forms.ValidationError("El proyecto es obligatorio.")
        return project

    # Validar tipo
    def clean_type(self):
        tipo = self.cleaned_data.get('type')
        if not tipo:
            raise forms.ValidationError("El tipo de transacción es obligatorio.")
        return tipo

    # Validar concepto
    def clean_concept(self):
        concept = self.cleaned_data.get('concept')
        if not concept:
            raise forms.ValidationError("El concepto es obligatorio.")
        return concept

