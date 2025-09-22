from django.db import models
from django.utils import timezone
from datetime import datetime


class Meeting(models.Model):
    title = models.CharField(
        "Título",
        max_length=200,
        help_text="Título de la reunión"
    )
    date = models.DateField("Fecha")
    start_time = models.TimeField("Hora de inicio")
    end_time = models.TimeField("Hora de fin")
    isActive = models.BooleanField("Reunión activa", default=True)

    def __str__(self):
        return f"{self.title} - {self.date}"

    @property
    def status(self):
        """Devuelve el estado actual de la reunión."""
        now = timezone.localtime()  # Fecha y hora actual
        meeting_end = timezone.make_aware(
            datetime.combine(self.date, self.end_time),
            timezone.get_current_timezone()
        )

        if not self.isActive:
            return "Suspendida"
        elif now >= meeting_end:
            return "Finalizada"
        return "Programada"
    

class Attendance(models.Model):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    partner = models.ForeignKey(
        'project.Partner',
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    def __str__(self):
        return f"{self.partner} - {self.meeting}"