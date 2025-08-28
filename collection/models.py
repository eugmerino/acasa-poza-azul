from django.db import models

class Fee(models.Model):
    short_description = models.CharField(
        "Descripción",
        max_length=200,
        help_text="Descripción corta de la tarifa"
    )
    approval_date = models.DateField("Fecha de aprobación")
    isActive = models.BooleanField("Tarifa activa", default=False)

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
        help_text="Metro mínimo para aplicar esta tramo"
    )
    max_meter = models.IntegerField(
        "Metro máximo",
        help_text="Metro máximo para aplicar esta tramo"
    )
    fixed_amount = models.DecimalField(
        "Monto fijo minimo",
        max_digits=10, decimal_places=2,
        help_text="Monto minimo fijo a cobrar en esta tramo"
    )
    amount_meter = models.DecimalField(
        "Monto por metro adicional",
        max_digits=10, decimal_places=2,
        help_text="Monto a cobrar por cada metro adicional al minimo"
    )

    def __str__(self):
        return f"{self.fee.short_description}: {self.min_value} - {self.max_value} m³"