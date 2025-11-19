def notificaciones_context(request):
    from repair.models import Repair
    from collection.models import Fee
    from django.urls import reverse
    from project.models import Project
    from meeting.models import Meeting 
    from django.utils.timezone import localtime
    from datetime import datetime, time

    project = Project.objects.first()

    # Si no hay usuario logueado -> no mostrar notificaciones
    if not request.user.is_authenticated:
        return {
            "notificaciones": [],
            "num_notificaciones": 0
        }

    notificaciones = []

    # 1. Mostrar alerta si NO hay una tarifa activa - SOLO para ADMINISTRADOR o SECRETARIO
    user_group = request.user.groups.first()
    if user_group and user_group.name in ["ADMINISTRADOR", "SECRETARIO"]:
        if not Fee.objects.filter(isActive=True).exists():
            notificaciones.append({
                "mensaje": "No se ha seleccionado ninguna tarifa activa.",
                "link": reverse("fee_list")
            })

    # 2. Verificar si hay una reunión en proceso
    now = localtime()
    current_time = now.time()
    current_date = now.date()

    # Buscar reuniones activas que estén en curso
    meeting_in_progress = Meeting.objects.filter(
        isActive=True,
        date=current_date,
        start_time__lte=current_time,
        end_time__gte=current_time
    ).first()

    if meeting_in_progress:
        notificaciones.append({
            "mensaje": f"Reunión en proceso: {meeting_in_progress.title}",
            "link": reverse("attendance")
        })

    # número total
    num_notificaciones = len(notificaciones)

    return {
        "notificaciones": notificaciones,
        "num_notificaciones": num_notificaciones,
        "project": project,
    }