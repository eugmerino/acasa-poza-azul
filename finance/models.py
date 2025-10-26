from django.db import models
from project.models import Project, WaterConnection


class Transaction(models.Model):
    TIPO_CHOICES = [
        ('I', 'Ingreso'),
        ('E', 'Egreso'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='transacciones'
    )
    concept = models.CharField(max_length=255)
    type = models.CharField(max_length=1, choices=TIPO_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()


    def __str__(self):
        return f"{self.get_type_display()} - {self.concept} (${self.amount})"


class Payment(models.Model):
    connection = models.ForeignKey(
        WaterConnection,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    date_pay = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Pago de ${self.amount} - acometida: {self.connection.description}"
