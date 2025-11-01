# finance/forms.py
from django import forms
from .models import Transaction, Project
from django.utils import timezone

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['project', 'concept', 'type', 'amount', 'date']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'concept': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Concepto de la transacción', 'required': True}),
            'type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0','required': True}),
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

     # 👇 AQUÍ ESTÁ EL BLOQUE CORRECTO
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si solo hay un proyecto, lo selecciona automáticamente
        projects = Project.objects.all()
        if projects.count() == 1:
            self.fields['project'].initial = projects.first()

        # Cambiar la etiqueta inicial del campo 'type'
        if self.fields['type'].choices:
            # Filtra para eliminar la opción vacía por defecto (las rayitas)
            choices = [(value, label) for value, label in self.fields['type'].choices if value != '']
            # Agrega nuestra opción inicial personalizada
            self.fields['type'].choices = [('', 'Seleccionar')] + choices



# forms.py
from django import forms
from django.db.models import Sum
from decimal import Decimal
from django.utils import timezone
from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["connection", "amount"]
        widgets = {
            "connection": forms.Select(
                attrs={
                    "id": "connection_hidden",
                    "style": "display:none;",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. 15.00",
                    "min": "0",
                    "step": "0.01",
                }
            ),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is None:
            return amount
        if amount <= 0:
            raise forms.ValidationError("El abono debe ser mayor a 0.")
        return amount

    def clean(self):
        cleaned = super().clean()
        connection = cleaned.get("connection")
        amount = cleaned.get("amount")
        if not connection or amount is None:
            return cleaned

        # 1 pago por mes
        ref_date = timezone.localdate()
        year, month = ref_date.year, ref_date.month
        if Payment.objects.filter(connection=connection,
                                  date_pay__year=year,
                                  date_pay__month=month).exists():
            self.add_error("connection", "Esta acometida ya tiene su pago correspondiente del mes.")
            return cleaned

        # (Mantén aquí tu chequeo de restante si ya lo tenías)
        total_pagado = (
            Payment.objects
            .filter(connection=connection)
            .exclude(pk=self.instance.pk)
            .aggregate(s=Sum('amount'))['s'] or Decimal('0')
        )
        precio = connection.acquisition_price or Decimal('0')
        restante = precio - total_pagado
        if restante <= 0:
            self.add_error("connection", "Esta acometida ya está completamente pagada.")
        elif amount > restante:
            self.add_error("amount", f"El abono excede el restante (${restante}).")

        return cleaned
