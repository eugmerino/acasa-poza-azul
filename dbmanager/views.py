import os
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.http import FileResponse, JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt


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
                "url": f"/dbmanager/download/{fname}",
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
# GENERAR BACKUP
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
        "-F", "p",  # plain SQL
        "-O",       # omite ownership de objetos (útil para evitar errores al restaurar)
        "-x",       # omite privilegios
        db["NAME"]
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = db["PASSWORD"]

    try:
        with open(backup_path, "w") as f:
            subprocess.run(command, env=env, stdout=f, check=True)
        messages.success(request, "Backup generado exitosamente (plain SQL completo).")
    except subprocess.CalledProcessError as e:
        messages.error(request, f"Error al generar backup: {e}")

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
# RESTAURAR BACKUP
# ======================================================
@csrf_exempt
def restore_backup(request, filename):
    backup_path = settings.BACKUP_DIR / filename
    if not backup_path.exists():
        messages.error(request, "El backup no existe.")
        return redirect("backup_list")

    db = get_db_settings()

    # Comando para dropear y crear la base
    drop_create_cmd = [
        "psql",
        "-h", db["HOST"],
        "-p", str(db["PORT"]),
        "-U", db["USER"],
        "-d", "postgres",  # conectamos a postgres para poder dropear la base
        "-c", f'DROP DATABASE IF EXISTS "{db["NAME"]}"; CREATE DATABASE "{db["NAME"]}";'
    ]

    restore_cmd = [
        "psql",
        "-h", db["HOST"],
        "-p", str(db["PORT"]),
        "-U", db["USER"],
        "-d", db["NAME"]
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = db["PASSWORD"]

    try:
        # 1️⃣ Dropear y crear base
        subprocess.run(drop_create_cmd, env=env, check=True)

        # 2️⃣ Restaurar backup
        with open(backup_path, "r") as f:
            subprocess.run(restore_cmd, env=env, stdin=f, check=True)

        messages.success(request, f"Base reemplazada y restaurada desde: {filename}")

    except subprocess.CalledProcessError as e:
        messages.error(request, f"Error al restaurar backup: {e}")

    return redirect("backup_list")