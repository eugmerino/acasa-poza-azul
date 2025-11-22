from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.conf import settings
import os


User = get_user_model()

GROUP_PERMISSIONS = {
    "ADMINISTRADOR": [
        ("audit", "logentry", ["view"]),
        ("project", "project", ["change", "view"]),
        ("project", "community", ["add", "change", "view"]),
        ("project", "partner", ["add", "change", "view"]),
        ("project", "directive", ["add", "change", "view"]),
        ("project", "waterconnection", ["add", "change", "view"]),
        ("collection", "fee", ["add", "view"]),
        ("collection", "range", ["add", "view"]),
        ("collection", "reading", ["add", "change", "view"]),
        ("finance", "transaction", ["add", "change", "view"]),
        ("finance", "payment", ["add", "change", "view"]),
        ("repair", "repair", ["add", "change", "view"]),
        ("meeting", "meeting", ["add", "change", "view"]),
        ("meeting", "attendance", ["add", "change", "view"]),
    ],
    "SECRETARIO": [
        ("project", "project", ["change", "view"]),
        ("project", "community", ["add", "change", "view"]),
        ("project", "partner", ["add", "change", "view"]),
        ("project", "directive", ["add", "change", "view"]),
        ("project", "waterconnection", ["add", "change", "view"]),
        ("collection", "fee", ["add", "view"]),
        ("collection", "range", ["add", "view"]),
        ("collection", "reading", ["add", "change", "view"]),
        ("finance", "transaction", ["view"]),
        ("finance", "payment", ["view"]),
        ("repair", "repair", ["add", "change", "view"]),
        ("meeting", "meeting", ["add", "change", "view"]),
        ("meeting", "attendance", ["add", "change", "view"]),
    ],
    "DIRECTIVO": [
        ("project", "project", ["view"]),
        ("project", "community", ["view"]),
        ("project", "partner", ["view"]),
        ("project", "directive", ["view"]),
        ("project", "waterconnection", ["view"]),
        ("collection", "fee", ["view"]),
        ("collection", "range", ["view"]),
        ("collection", "reading", ["view"]),
        ("finance", "transaction", ["view"]),
        ("finance", "payment", ["view"]),
        ("repair", "repair", ["view"]),
        ("meeting", "meeting", ["view"]),
        ("meeting", "attendance", ["change", "view"]),
    ],
    "CONTADOR": [
        ("finance", "transaction", ["add", "change", "view"]),
        ("finance", "payment", ["add", "change", "view"]),
        ("repair", "repair", ["view"]),
        ("meeting", "meeting", ["view"]),
        ("meeting", "attendance", ["add", "change", "view"]),
    ],
    "LECTOR": [
        ("collection", "reading", ["add", "change", "view"]),
        ("repair", "repair", ["view"]),
        ("meeting", "meeting", ["view"]),
        ("meeting", "attendance", ["add", "change", "view"]),
    ],
    "COLECTOR": [
        ("collection", "reading", ["add", "change", "view"]),
        ("repair", "repair", ["view"]),
        ("meeting", "meeting", ["view"]),
        ("meeting", "attendance", ["add", "change", "view"]),
    ],
    "FONTANERO": [
        ("repair", "repair", ["add", "change", "view"]),
        ("meeting", "meeting", ["view"]),
        ("meeting", "attendance", ["add", "change", "view"]),
    ]
}

@receiver(post_migrate)
def create_default_groups_and_superuser(sender, **kwargs):

    if kwargs.get("interactive", True) is False:
        return

    if os.environ.get("RUN_MAIN") == "true":
        return

    # Crear grupos
    for group_name in GROUP_PERMISSIONS.keys():
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f'✅ Grupo "{group_name}" creado.')

        # Asignar permisos al grupo
        for app_label, model_name, perms in GROUP_PERMISSIONS[group_name]:
            for perm in perms:
                codename = f"{perm}_{model_name}"
                try:
                    permission = Permission.objects.get(
                        codename=codename,
                        content_type__app_label=app_label,
                        content_type__model=model_name
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"⚠️ Permiso no encontrado: {codename}")

    # Crear superusuario por defecto
    if not User.objects.filter(username='developer').exists():
        user = User.objects.create_superuser(
            username='developer',
            email='developer@example.com',
            password='default'
        )
        admin_group = Group.objects.get(name='ADMINISTRADOR')
        user.groups.add(admin_group)
        print('✅ Superusuario "developer" creado y asignado.')