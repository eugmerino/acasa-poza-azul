def notificaciones_context(request):
    from repair.models import Repair
    from collection.models import Fee

    # Si no hay usuario logueado -> no mostrar notificaciones
    if not request.user.is_authenticated:
        return {
            "notificaciones": [],
            "num_notificaciones": 0
        }

    # EJEMPLO: notificación sin modelo  
    # Puedes agregar más reglas si quieres.
    notificaciones = []

    # 1. Mostrar alerta si NO hay una tarifa activa
    if not Fee.objects.filter(isActive=True).exists():
        notificaciones.append({
            "mensaje": "No hay una tarifa activa configurada.",
            "link": "/fees/"
        })


    pendientes = Repair.objects.filter(fixed=False).count()
    if pendientes > 0:
        notificaciones.append({
            "mensaje": f"Tienes {pendientes} reparaciones pendientes.",
            "link": "/repairs/"
        })

    # número total
    num_notificaciones = len(notificaciones)

    return {
        "notificaciones": notificaciones,
        "num_notificaciones": num_notificaciones,
    }
