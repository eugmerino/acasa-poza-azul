from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.conf import settings
import os


User = get_user_model()

@receiver(post_migrate)
def create_default_groups_and_superuser(sender, **kwargs):
    """
    Crea los grupos y el superusuario por defecto SOLO cuando
    se ejecuta migrate MANUALMENTE, no en cada arranque del servidor.
    """

    # Evitar ejecución en runserver / producción
    # Solo correr cuando se llame explicitamente a "python manage.py migrate"
    if kwargs.get("interactive", True) is False:
        return

    # Evitar ejecución doble del autoreloader en runserver
    if os.environ.get("RUN_MAIN") == "true":
        return

    group_names = [
        'ADMINISTRADOR',
        'SECRETARIO',
        'DIRECTIVO',
        'CONTADOR',
        'LECTOR',
        'COLECTOR',
        'FONTANERO'
    ]

    for name in group_names:
        group, created = Group.objects.get_or_create(name=name)
        if created:
            print(f'✅ Grupo "{name}" creado correctamente.')

    # Crear superusuario si no existe
    if not User.objects.filter(username='developer').exists():
        user = User.objects.create_superuser(
            username='developer',
            email='developer@example.com',
            password='default'
        )
        admin_group = Group.objects.get(name='ADMINISTRADOR')
        user.groups.add(admin_group)
        print('✅ Superusuario "developer" creado y asignado.')
