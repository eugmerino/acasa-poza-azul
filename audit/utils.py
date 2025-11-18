from .models import LogEntry

def registrar_log(
    user,
    action: str,
    model_name: str,
    object_id=None,
    description: str = ""
):
    """
    Registra una entrada en la bitácora del sistema.

    Parámetros:
    - user: instancia del usuario (Partner).
    - action: str ('create', 'update', 'delete', 'login', 'logout', 'other').
    - model_name: nombre del modelo donde ocurrió la acción.
    - object_id: id del objeto afectado o titulo.
    - description: texto descriptivo de la acción.
    """

    LogEntry.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        description=description,
    )
