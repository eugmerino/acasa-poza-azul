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
from django.db import connection
import psycopg2
from psycopg2 import sql


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

    # Crear directorio si no existe
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    for fname in os.listdir(backup_dir):
        path = Path(backup_dir) / fname
        if path.is_file() and fname.endswith('.sql'):
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
# GENERAR BACKUP (MEJORADO)
# ======================================================
@csrf_exempt
def generate_backup(request):
    db = get_db_settings()
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"
    backup_path = settings.BACKUP_DIR / filename

    # Crear directorio si no existe
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "pg_dump",
        "-h", db["HOST"],
        "-p", str(db["PORT"]),
        "-U", db["USER"],
        "-F", "p",
        "-O",  # No owner
        "-x",  # No privileges
        "--clean",  # Incluye DROP statements
        db["NAME"]
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = db["PASSWORD"]

    try:
        with open(backup_path, "w") as f:
            result = subprocess.run(
                command, 
                env=env, 
                stdout=f, 
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        
        # Verificar que el backup se creó correctamente
        if backup_path.stat().st_size > 0:
            messages.success(request, f"Backup generado: {filename}")
        else:
            messages.error(request, "El backup se generó vacío")
            backup_path.unlink(missing_ok=True)
            
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        messages.error(request, f"Error al generar backup: {error_msg}")
        backup_path.unlink(missing_ok=True)
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
        backup_path.unlink(missing_ok=True)

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
# RESTAURAR BACKUP (SOLUCIÓN CORREGIDA)
# ======================================================
@csrf_exempt
def restore_backup(request, filename):
    backup_path = settings.BACKUP_DIR / filename
    if not backup_path.exists():
        messages.error(request, "El backup no existe.")
        return redirect("backup_list")

    db = get_db_settings()
    
    # Verificar que el archivo no esté vacío
    if backup_path.stat().st_size == 0:
        messages.error(request, "El archivo de backup está vacío.")
        return redirect("backup_list")

    env = os.environ.copy()
    env["PGPASSWORD"] = db["PASSWORD"]

    try:
        # 1️⃣ Cerrar todas las conexiones a la base de datos actual
        close_connections_command = [
            "psql",
            "-h", db["HOST"],
            "-p", str(db["PORT"]),
            "-U", db["USER"],
            "-d", "postgres",
            "-c", f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db['NAME']}'
            AND pid <> pg_backend_pid();
            """
        ]
        
        subprocess.run(close_connections_command, env=env, capture_output=True)

        # 2️⃣ Dropear y recrear la base de datos
        recreate_db_command = [
            "psql", 
            "-h", db["HOST"],
            "-p", str(db["PORT"]),
            "-U", db["USER"],
            "-d", "postgres",
            "-c", f"DROP DATABASE IF EXISTS \"{db['NAME']}\"; CREATE DATABASE \"{db['NAME']}\";"
        ]
        
        result = subprocess.run(
            recreate_db_command, 
            env=env, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            messages.error(request, f"Error al recrear BD: {result.stderr}")
            return redirect("backup_list")

        # 3️⃣ Restaurar el backup
        restore_command = [
            "psql",
            "-h", db["HOST"],
            "-p", str(db["PORT"]),
            "-U", db["USER"],
            "-d", db["NAME"],
            "-f", str(backup_path)  # Usar -f en lugar de stdin
        ]

        result = subprocess.run(
            restore_command, 
            env=env, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minutos timeout
        )

        if result.returncode == 0:
            messages.success(request, f"Base de datos restaurada exitosamente desde: {filename}")
        else:
            error_detail = result.stderr[:500] if result.stderr else "Error desconocido"
            messages.error(request, f"Error en restauración: {error_detail}")

    except subprocess.TimeoutExpired:
        messages.error(request, "La restauración tomó demasiado tiempo (timeout)")
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")

    if request.headers.get("HX-Request") == "true":
        return backups_list(request)
    return redirect("backup_list")


# ======================================================
# VERIFICAR CONEXIÓN (PARA DEBUGGING)
# ======================================================
def test_db_connection():
    """Función para verificar que podemos conectarnos a PostgreSQL"""
    db = get_db_settings()
    command = [
        "psql",
        "-h", db["HOST"],
        "-p", str(db["PORT"]),
        "-U", db["USER"],
        "-d", "postgres",
        "-c", "SELECT version();"
    ]
    
    env = os.environ.copy()
    env["PGPASSWORD"] = db["PASSWORD"]
    
    try:
        result = subprocess.run(command, env=env, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False