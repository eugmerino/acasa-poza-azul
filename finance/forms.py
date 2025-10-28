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
