from django.db import models


class Project(models.Model):
    title = models.CharField(
        "Titulo",
        max_length=200,
        help_text="Titulo del proyecto",
    )
    description = models.TextField("Descripción")
    logo = models.ImageField(
        "Logo",
        upload_to='project_logos/',
        null=True,
        blank=True
    )
    connection_price = models.DecimalField(
        "Precio de acometida",
        max_digits=10, decimal_places=2
    )
    absence_fine = models.DecimalField(
        "Multa por ausencia a reunión",
        max_digits=10, decimal_places=2
    )

    def __str__(self):
        return self.title
    

class community(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='communities'
    )
    name = models.CharField(
        "Nombre",
        max_length=200,
        help_text="Nombre de la comunidad"
    )
    description = models.TextField("Descripción")

    def __str__(self):
        return self.name
    

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