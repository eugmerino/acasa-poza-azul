from django.contrib.auth.models import AbstractUser
from django.db import models


class Project(models.Model):
    title = models.CharField(
        "Titulo",
        max_length=50,
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
    

class Community(models.Model):
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
    

class Partner(AbstractUser):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='partners'
    )
    dui = models.CharField(max_length=10, unique=True, blank=True, null=True)
    tel = models.CharField(max_length=15, blank=True, null=True)
    foto = models.ImageField(upload_to="users/", blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    

from django.db import models
from project.models import Partner  # ajusta la importación según tu estructura


class Directive(models.Model):
    class Roles(models.TextChoices):
        PRESIDENTE = "PRESIDENTE", "Presidente"
        VICEPRESIDENTE = "VICEPRESIDENTE", "Vicepresidente"
        SINDICO = "SINDICO", "Síndico"
        SECRETARIO = "SECRETARIO", "Secretario"
        TESORERO = "TESORERO", "Tesorero"
        VOCAL = "VOCAL", "Vocal"

    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="directives"
    )
    role = models.CharField(
        "Cargo",
        max_length=20,
        choices=Roles.choices
    )
    start_date = models.DateField("Fecha de inicio del período")

    def __str__(self):
        return f"{self.partner} - {self.get_role_display()} ({self.start_date})"

    