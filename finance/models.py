from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
from project.models import Project, WaterConnection
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce


class Transaction(models.Model):
    TIPO_CHOICES = [
        ('I', 'Ingreso'),
        ('E', 'Egreso'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='transacciones')
    concept = models.CharField(max_length=255)
    type = models.CharField(max_length=1, choices=TIPO_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.concept} (${self.amount})"


class Payment(models.Model):
    connection = models.ForeignKey(WaterConnection, on_delete=models.CASCADE, related_name='payments')
    date_pay = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Pago de ${self.amount} - acometida: {self.connection.description}"

    def clean(self):
        super().clean()
        if not self.connection_id or self.amount is None:
            return

        # === Restricción: solo 1 pago por acometida en el mes ===
        ref_date = self.date_pay or timezone.localdate()
        year, month = ref_date.year, ref_date.month

        ya_tiene_pago_en_mes = (
            Payment.objects
            .filter(connection=self.connection,
                    date_pay__year=year,
                    date_pay__month=month)
            .exclude(pk=self.pk)
            .exists()
        )
        if ya_tiene_pago_en_mes:
            raise ValidationError({
                'connection': 'Esta acometida ya tiene su pago correspondiente del mes.'
            })

        # === (si ya tenías estas reglas, mantenlas) ===
        total_pagado = (
            Payment.objects
            .filter(connection=self.connection)
            .exclude(pk=self.pk)
            .aggregate(s=Sum('amount'))['s'] or Decimal('0')
        )
        precio = self.connection.acquisition_price or Decimal('0')
        restante = precio - total_pagado

        if restante <= 0:
            raise ValidationError({'connection': 'Esta acometida ya está completamente pagada.'})

        if self.amount > restante:
            raise ValidationError({'amount': f'El abono excede el restante (${restante}).'})
        
    @staticmethod
    def total_pagado_por_acometida(payment):
        return (
            Payment.objects
            .filter(
                connection=payment.connection,
                date_pay__lte=payment.date_pay 
            )
            .aggregate(
                total=Coalesce(
                    Sum("amount"),
                    Value(Decimal("0"), output_field=DecimalField())
                )
            )["total"]
        )
