from django.db import models
from project.models import Partner

class LogEntry(models.Model):
    ACTIONS = [
        ("create", "Creación"),
        ("update", "Actualización"),
        ("delete", "Eliminación"),
        ("login", "Inicio de sesión"),
        ("logout", "Cierre de sesión"),
        ("other", "Otro"),
    ]

    user = models.ForeignKey( # Usuario que realizó la acción
        Partner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=20, choices=ACTIONS) # Tipo de acción realizada
    model_name = models.CharField(max_length=100) # Nombre del modelo afectado
    object_id = models.CharField(max_length=50, null=True, blank=True) # ID del objeto afectado
    description = models.TextField() # Descripción detallada de la acción
    created_at = models.DateTimeField(auto_now_add=True) # Fecha y hora de la acción

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} ({self.created_at})"
