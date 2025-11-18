from django.db import models
from project.models import WaterConnection
from django.utils import timezone
from decimal import Decimal
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
    

    @classmethod
    def has_active(cls) -> bool:
        """Devuelve True si existe al menos una tarifa activa."""
        return cls.objects.filter(isActive=True).exists()
        

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


class Reading(models.Model):
    connection = models.ForeignKey(
        WaterConnection,
        on_delete=models.CASCADE,
        related_name='readings',
        verbose_name='Acometida de agua'
    )
    fee = models.ForeignKey(
        Fee,
        on_delete=models.CASCADE,
        related_name='readings',
        verbose_name='Tarifa aplicada',
        null=True,
        blank=True
    )
    date_reading = models.DateField(
        "Fecha de lectura",
        null=True,
        blank=True
    )
    receipt_number = models.CharField(
        "Número de recibo",
        max_length=100,
        unique=True
    )
    meter_reading = models.IntegerField(
        "Lectura del medidor",
        help_text="Valor de la lectura del medidor en m³"
    )
    previous_reading = models.IntegerField(
        "Lectura anterior",
        help_text="Valor de la lectura anterior del medidor en m³",
        null=True,
        blank=True
    )
    penalty_fee = models.DecimalField(
        "Multa por ausencia a reunión",
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    late_payment = models.DecimalField(  
        "Mora",
        max_digits=10,
        decimal_places=2,
        default=0.00,
        null=True,
        blank=True
    )
    isPaid = models.BooleanField(
        "Cobrado",
        default=False
    )

    def save(self, *args, **kwargs):
        # Si no tiene fecha asignada, usar la fecha local actual
        if not self.date_reading:
            self.date_reading = timezone.localtime().date()

        # Si no hay tarifa activa asignada
        if not self.fee_id:
            active_fee = Fee.objects.filter(isActive=True).first()
            if active_fee:
                self.fee = active_fee
            else:
                raise ValueError("No existe una tarifa activa. Debe registrar o activar una tarifa antes de continuar.")

        # Si no hay lectura anterior registrada
        if self.previous_reading is None:
            last_reading = (
                Reading.objects
                .filter(connection=self.connection)
                .exclude(pk=self.pk)
                .order_by('-date_reading')
                .first()
            )
            self.previous_reading = last_reading.meter_reading if last_reading else 0.00

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Lectura {self.meter_reading} m³ - Acometida: {self.connection.description}"


    @staticmethod
    def calculate_unpaid_total(connection):
        """
        Retorna un diccionario con:
        - total_amount: monto total acumulado de lecturas impagas
        - total_penalties: total de multas acumuladas
        - total_to_pay: suma total a pagar (lecturas + multas)
        - last_paid_reading: última lectura pagada encontrada
        - last_reading: última lectura registrada
        """
        today = timezone.localtime().date()

        unpaid_total = Decimal("0.00")
        penalty_total = Decimal("0.00")
        last_paid = None
        total_unpaid = 0

        # Lecturas ordenadas de la más reciente a la más antigua(excluyendo las del corriente mes)
        readings = (
            Reading.objects
            .filter(connection=connection)
            .exclude(date_reading__year=today.year, date_reading__month=today.month)
            .order_by("-date_reading")
        )
        if not readings.exists():
            return None

        last_reading = readings.first()

        for reading in readings:
            if reading.isPaid:
                last_paid = reading
                break
            else:
                # Sumar la multa
                penalty_total += reading.penalty_fee

                # Calcular consumo usando previous_reading
                metros_consumidos = reading.meter_reading - (reading.previous_reading or 0)
                monto = Reading.calculate_amount(reading.fee, metros_consumidos)
                unpaid_total += monto
                total_unpaid += 1

        return {
            "total_amount": unpaid_total,
            "total_penalties": penalty_total,
            "total_to_pay": unpaid_total + penalty_total,
            "last_paid_reading": last_paid,
            "last_reading": last_reading,
            "total_unpaid": total_unpaid,
        }
    
    @staticmethod
    def calculate_previous_unpaid_total(reading):
        """
        Retorna un diccionario con:
        - total_amount: monto total acumulado de lecturas impagas anteriores a la lectura dada
        - total_penalties: total de multas acumuladas
        - total_to_pay: suma total a pagar (lecturas + multas)
        - last_paid_reading: última lectura pagada encontrada
        - last_reading: última lectura registrada antes de la lectura actual
        - total_unpaid: cantidad de lecturas impagas anteriores
        """

        if not reading or not reading.connection:
            return None

        unpaid_total = Decimal("0.00")
        penalty_total = Decimal("0.00")
        last_paid = None
        total_unpaid = 0

        # 🔹 Obtenemos la fecha de la lectura actual
        date_ref = reading.date_reading

        if not date_ref:
            return None

        # 🔹 Filtramos solo las lecturas ANTERIORES a la fecha de la lectura actual
        readings = (
            Reading.objects
            .filter(
                connection=reading.connection
            )
            .exclude(
                Q(date_reading__year__gt=date_ref.year) |
                Q(date_reading__year=date_ref.year, date_reading__month__gte=date_ref.month)
            )
            .order_by("-date_reading")
        )

        if not readings.exists():
            return None

        last_reading = readings.first()

        for r in readings:
            if r.isPaid:
                last_paid = r
                break
            else:
                # 🔹 Sumar multa
                penalty_total += r.penalty_fee

                # 🔹 Calcular consumo
                metros_consumidos = r.meter_reading - (r.previous_reading or 0)
                monto = Reading.calculate_amount(r.fee, metros_consumidos)
                unpaid_total += monto
                total_unpaid += 1

        return {
            "total_amount": unpaid_total,
            "total_penalties": penalty_total,
            "total_to_pay": unpaid_total + penalty_total,
            "last_paid_reading": last_paid,
            "last_reading": last_reading,
            "total_unpaid": total_unpaid,
        }


    @staticmethod
    def calculate_amount(fee, metros):
        """
        Calcula el monto a pagar en base a los tramos (Range) de la tarifa.
        """
        tramo = None
        for r in fee.Fee_ranges.all().order_by("min_meter"):
            if r.max_meter is not None:
                if r.min_meter <= metros <= r.max_meter:
                    tramo = r
                    break
            else:
                if metros >= r.min_meter:
                    tramo = r
                    break

        if not tramo:
            raise ValueError(f"No existe un tramo válido para {metros} m³")

        monto = Decimal(tramo.fixed_amount)
        metros_extra = metros - tramo.min_meter
        if metros_extra > 0 and tramo.amount_meter:
            monto += Decimal(metros_extra) * Decimal(tramo.amount_meter)

        return monto
