import os
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse


def get_db_settings():
    db = settings.DATABASES["default"]
    return {
        "NAME": db["NAME"],
        "USER": db["USER"],
        "PASSWORD": db["PASSWORD"],
        "HOST": db["HOST"],
        "PORT": db["PORT"],
    }


# ======================================================
# LISTAR BACKUPS (paginar + buscar + HTMX)
# ======================================================
def backups_list(request):
    backup_dir = settings.BACKUP_DIR
    files = []

    for fname in os.listdir(backup_dir):
        path = Path(backup_dir) / fname
        if path.is_file():
            files.append({
                "name": fname,
                "size": path.stat().st_size,
                "created": timezone.datetime.fromtimestamp(path.stat().st_mtime),
                "url": reverse("download_backup", args=[fname]),
            })

    # Búsqueda
    q = request.GET.get("q", "")
    if q:
        files = [f for f in files if q.lower() in f["name"].lower()]

    # Ordenar por fecha desc
    files = sorted(files, key=lambda x: x["created"], reverse=True)

    paginator = Paginator(files, 10)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    context = {
        "page_obj": page_obj,
        "backups_search_url": request.path,
        "per_page_options": [10, 20, 50],
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "backups/partials/backups_table.html", context)

    return render(request, "backups/backups.html", context)


# ======================================================
# GENERAR BACKUP (agregando --clean para restauraciones seguras)
# ======================================================
@csrf_exempt
def generate_backup(request):
    db = get_db_settings()
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"
    backup_path = settings.BACKUP_DIR / filename

    command = [
        "pg_dump",
        "-h", db["HOST"],
        "-p", str(db["PORT"]),
        "-U", db["USER"],
        "-F", "p",
        "--clean",       # <-- elimina objetos existentes antes de recrearlos
        "--if-exists",   # <-- solo elimina si existen
        db["NAME"],
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = db["PASSWORD"]

    try:
        with open(backup_path, "w") as f:
            subprocess.run(command, env=env, stdout=f, check=True)
        messages.success(request, "Backup generado exitosamente.")
    except Exception:
        messages.error(request, "Error al generar el backup.")

    if request.headers.get("HX-Request") == "true":
        return backups_list(request)

    return redirect("backup_list")


# ======================================================
# DESCARGAR BACKUP
# ======================================================
def download_backup(request, filename):
    path = settings.BACKUP_DIR / filename
    if not path.exists():
        messages.error(request, "El archivo no existe.")
        return redirect("backup_list")
    return FileResponse(open(path, "rb"), as_attachment=True, filename=filename)


# ======================================================
# RESTAURAR BACKUP usando psql con --clean
# ======================================================
@csrf_exempt
def restore_backup(request, filename):
    """
    Restaura un backup SQL sobre la base de datos actual de forma segura:
    - Usa los DROP existentes en el backup (--clean) para eliminar conflictos
    - Evita dropdb para no afectar conexiones activas
    """
    path = settings.BACKUP_DIR / filename
    if not path.exists():
        messages.error(request, "El backup no existe.")
        return redirect("backup_list")

    db = get_db_settings()
    env = os.environ.copy()
    env["PGPASSWORD"] = db["PASSWORD"]

    try:
        subprocess.run([
            "psql",
            "-h", db["HOST"],
            "-p", str(db["PORT"]),
            "-U", db["USER"],
            "-d", db["NAME"],
            "-f", str(path)
        ], env=env, check=True)
        messages.success(request, f"Base de datos restaurada correctamente desde: {filename}")
    except subprocess.CalledProcessError as e:
        messages.error(request, f"Error al restaurar el backup: {e}")

    # Si la petición viene de HTMX, devolvemos la tabla de backups
    if request.headers.get("HX-Request") == "true":
        from .views import backups_list
        return backups_list(request)

    return redirect("backup_list")
