from django.db import models

class Meeting(models.Model):
    title = models.CharField(
        "Titulo",
        max_length=200,
        help_text="Titulo de la reunion"
    )
    date = models.DateField("Fecha")
    start_time = models.TimeField("Hora de inicio")
    end_time = models.TimeField("Hora de fin")
    isActive = models.BooleanField("Reunion activa", default=True)

    def __str__(self):
        return f"{self.title} - {self.date} from {self.start_time} to {self.end_time}"