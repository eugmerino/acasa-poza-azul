from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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
    
    def save(self, *args, **kwargs):
        # Generar username si no existe
        if not self.username:
            first_part = self.first_name.split(" ")[0].lower() if self.first_name else ""
            last_part = self.last_name.split(" ")[0].lower() if self.last_name else ""
            base_username = f"{first_part}{last_part}"

            username = base_username
            counter = 1
            while Partner.objects.filter(username=username).exists():
                counter += 1
                username = f"{base_username}{counter}"

            self.username = username

        # Generar contraseña por defecto en formato "key:<dui>"
        if self.dui and not self.pk:  # solo al crear
            raw_password = f"key:{self.dui}"
            self.set_password(raw_password)

        # Si is_active = False → también is_staff = False
        if not self.is_active and self.is_staff:
            self.is_staff = False

        super().save(*args, **kwargs)


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
    isActive = models.BooleanField("Activo", default=True)
    start_date = models.DateField("Fecha de inicio del período")
    end_date = models.DateField(
        "Fecha de fin del período",
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        today = timezone.localtime().date()

        is_create = self.pk is None

        # Solo al crear: queda activo y sin fecha fin
        if is_create:
            self.isActive = True
            self.end_date = None
            if not self.start_date:
                self.start_date = today

        super().save(*args, **kwargs)

        # Solo al crear: desactivar anteriores del mismo cargo (si aplica)
        if is_create and self.role != self.Roles.VOCAL:
            (Directive.objects
                .filter(role=self.role, isActive=True)
                .exclude(pk=self.pk)
                .update(isActive=False, end_date=today))


def today_local():
    """Devuelve la fecha local actual."""
    return timezone.localtime().date()

class WaterConnection(models.Model):
    owner = models.ForeignKey(
        'Partner',
        on_delete=models.CASCADE,
        related_name='owned_connections',
        verbose_name='Propietario'
    )
    responsible = models.ForeignKey(
        'Partner',
        on_delete=models.CASCADE,
        related_name='responsible_connections',
        verbose_name='Responsable'
    )
    date = models.DateField(
        "Fecha de adquisición",
        default=today_local,
    )
    description = models.CharField(
        "Descripción",
        max_length=200,
        help_text="Descripción corta",
        unique=True,
    )
    is_active = models.BooleanField(
        "Activa",
        default=False,
    )
    acquisition_price = models.DecimalField(
        "Precio de adquisición",
        max_digits=12,
        decimal_places=2,
    )

    def save(self, *args, **kwargs):
        if not self.responsible:
            self.responsible = self.owner
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - {self.responsible.first_name} {self.responsible.last_name}"


    class Meta:
        verbose_name = "Acometida"
        verbose_name_plural = "Acometidas"
        ordering = ['-date']


