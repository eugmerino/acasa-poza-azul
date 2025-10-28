from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.dispatch import receiver

User = get_user_model()

@receiver(post_migrate)
def create_default_groups_and_superuser(sender, **kwargs):
    """
    Crea los grupos y el superusuario por defecto después de aplicar migraciones.
    """
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
        else:
            print(f'ℹ️ Grupo "{name}" ya existe.')

    # Crear superusuario developer si no existe
    if not User.objects.filter(username='developer').exists():
        user = User.objects.create_superuser(
            username='developer',
            email='developer@example.com',
            password='default'
        )
        print('✅ Superusuario "developer" creado.')

        admin_group = Group.objects.get(name='ADMINISTRADOR')
        user.groups.add(admin_group)
        print('✅ Superusuario "developer" agregado al grupo "ADMINISTRADOR".')
    else:
        print('ℹ️ El superusuario "developer" ya existe.')
