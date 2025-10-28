from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Project

@receiver(post_migrate)
def create_default_project(sender, **kwargs):
    """
    Crea un proyecto por defecto si no existe ninguno.
    """
    if not Project.objects.exists():
        Project.objects.create(
            title="ACASA Poza Azul",
            description="Proyecto inicial del sistema.",
            connection_price=0.00,
            absence_fine=0.00,
        )
        print("✅ Proyecto por defecto creado correctamente.")
    else:
        print("ℹ️ Ya existe al menos un proyecto. No se creó otro.")
