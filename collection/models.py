from django.db import models
from django.db.models import Q


class Fee(models.Model):
    short_description = models.CharField(
        "Descripción",
        max_length=200,
        help_text="Descripción corta de la tarifa",
        unique=True
    )
    approval_date = models.DateField(
        "Fecha de aprobación",
        unique=True
    )
    isActive = models.BooleanField("Tarifa activa", default=False)

    def save(self, *args, **kwargs):
        if self.isActive:
            # Si esta se activa, desactiva las demás
            Fee.objects.filter(isActive=True).exclude(pk=self.pk).update(isActive=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.short_description

    

class Range(models.Model):
    fee = models.ForeignKey(
        Fee,
        on_delete=models.CASCADE,
        related_name='Fee_ranges'
    )
    min_meter = models.IntegerField(
        "Metro mínimo",
        help_text="Metro mínimo para aplicar el tramo"
    )
    max_meter = models.IntegerField(
        "Metro máximo",
        help_text="Metro máximo para aplicar el tramo",
        null=True,
        blank=True
    )
    fixed_amount = models.DecimalField(
        "Monto fijo minimo",
        max_digits=10, decimal_places=2,
        help_text="Monto minimo fijo a cobrar en el tramo"
    )
    amount_meter = models.DecimalField(
        "Monto por metro adicional",
        max_digits=10, decimal_places=2,
        help_text="Monto a cobrar por cada metro adicional al metro minimo",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.fee.short_description}: {self.min_meter} - {self.max_meter} m³"