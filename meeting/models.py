from django.db import models


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
    