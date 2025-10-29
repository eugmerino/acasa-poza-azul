from django.db import models
from project.models import Community

class Repair(models.Model):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='repairs',
        verbose_name='Comunidad'
    )

    # Datos del reporte inicial
    report_title = models.CharField(
        max_length=200,
        verbose_name='Título del reporte'
    )
    report_date = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha del reporte'
    )
    report_description = models.TextField(
        verbose_name='Descripción del reporte'
    )
    report_photo = models.ImageField(
        upload_to='repairs/reports/',
        verbose_name='Foto del reporte'
    )

    # Datos de la reparación
    repair_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de reparación'
    )
    repair_description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descripción de la reparación'
    )
    repair_photo = models.ImageField(
        upload_to='repairs/fixes/',
        null=True,
        blank=True,
        verbose_name='Foto de la reparación'
    )

    # Datos de pago
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Monto del pago'
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de pago'
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name='Pagado'
    )

    class Meta:
        verbose_name = 'Reparación'
        verbose_name_plural = 'Reparaciones'
        ordering = ['-report_date']

    def __str__(self):
        return f"{self.report_title} - {self.community.name}"
    
    def save(self, *args, **kwargs):
        if self.payment_amount:
            self.is_paid = True
        else:
            self.is_paid = False
        super().save(*args, **kwargs)
