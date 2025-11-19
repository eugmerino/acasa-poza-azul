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
from io import StringIO
import json


def get_db_settings():
    db = settings.DATABASES["default"]
    return {
        "NAME": db["NAME"],
        "USER": db["USER"],
        "PASSWORD": db["PASSWORD"],
        "HOST": db["HOST"],
        "PORT": db["PORT"],
    }


def get_db_url():
    """Obtener URL de conexión para pg_dump"""
    db = get_db_settings()
    return f"postgresql://{db['USER']}:{db['PASSWORD']}@{db['HOST']}:{db['PORT']}/{db['NAME']}"


# ======================================================
# LISTAR BACKUPS
# ======================================================
def backups_list(request):
    backup_dir = settings.BACKUP_DIR
    files = []

    if backup_dir.exists():
        for fname in os.listdir(backup_dir):
            path = Path(backup_dir) / fname
            if path.is_file() and fname.endswith(('.sql', '.json', '.backup')):
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
# GENERAR BACKUP - VERSIÓN MEJORADA
# ======================================================
@csrf_exempt
def generate_backup(request):
    db = get_db_settings()
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    
    # Intentar diferentes métodos
    methods = [
        _try_pg_dump_backup,
        _try_django_backup,
        _try_simple_sql_backup
    ]
    
    success = False
    error_messages = []
    
    for method in methods:
        try:
            result = method(db, timestamp)
            if result:
                messages.success(request, f"Backup generado: {result}")
                success = True
                break
        except Exception as e:
            error_messages.append(f"{method.__name__}: {str(e)}")
    
    if not success:
        messages.error(request, f"Error al generar backup. Métodos intentados: {' | '.join(error_messages)}")
    
    return redirect("backup_list")


def _try_pg_dump_backup(db, timestamp):
    """Intentar backup con pg_dump"""
    filename = f"backup_{timestamp}.sql"
    backup_path = settings.BACKUP_DIR / filename
    
    # Verificar si pg_dump está disponible
    try:
        subprocess.run(["pg_dump", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    
    command = [
        "pg_dump",
        "--dbname", f"postgresql://{db['USER']}:{db['PASSWORD']}@{db['HOST']}:{db['PORT']}/{db['NAME']}",
        "--no-owner",
        "--no-privileges",
        "--verbose"
    ]
    
    try:
        with open(backup_path, "w") as f:
            result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True, timeout=300)
            if result.returncode != 0:
                raise Exception(result.stderr)
        return filename
    except Exception as e:
        # Si falla, eliminar archivo parcial
        if backup_path.exists():
            backup_path.unlink()
        raise e


def _try_django_backup(db, timestamp):
    """Backup usando Django ORM (solo datos)"""
    from django.core import serializers
    from django.apps import apps
    
    filename = f"backup_{timestamp}.json"
    backup_path = settings.BACKUP_DIR / filename
    
    try:
        all_models = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                try:
                    data = serializers.serialize("json", model.objects.all())
                    all_models.append({
                        'app': app_config.label,
                        'model': model.__name__,
                        'data': json.loads(data)
                    })
                except Exception as e:
                    print(f"Error serializando {model}: {e}")
                    continue
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(all_models, f, indent=2, ensure_ascii=False)
        
        return filename
    except Exception as e:
        if backup_path.exists():
            backup_path.unlink()
        raise e


def _try_simple_sql_backup(db, timestamp):
    """Backup básico de tablas esenciales"""
    filename = f"backup_essential_{timestamp}.sql"
    backup_path = settings.BACKUP_DIR / filename
    
    try:
        with connection.cursor() as cursor:
            # Obtener todas las tablas
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
        
        sql_content = []
        for table in tables:
            # Backup de estructura (simplificado)
            sql_content.append(f"-- Backup de tabla: {table}\n")
            
            # Backup de datos
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{table}"')
                columns = [desc[0] for desc in cursor.description]
                
                for row in cursor.fetchall():
                    values = []
                    for value in row:
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, str):
                            values.append(f"'{value.replace("'", "''")}'")
                        else:
                            values.append(str(value))
                    
                    sql_content.append(
                        f'INSERT INTO "{table}" ({", ".join(columns)}) '
                        f'VALUES ({", ".join(values)});\n'
                    )
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_content))
        
        return filename
    except Exception as e:
        if backup_path.exists():
            backup_path.unlink()
        raise e


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
# RESTAURAR BACKUP - VERSIÓN MEJORADA
# ======================================================
@csrf_exempt
def restore_backup(request, filename):
    backup_path = settings.BACKUP_DIR / filename
    if not backup_path.exists():
        messages.error(request, "El backup no existe.")
        return redirect("backup_list")

    try:
        if filename.endswith('.json'):
            _restore_json_backup(backup_path)
        elif filename.endswith('.sql'):
            _restore_sql_backup(backup_path)
        else:
            messages.error(request, "Formato de backup no soportado.")
            return redirect("backup_list")
        
        messages.success(request, f"Backup restaurado exitosamente: {filename}")
        
    except Exception as e:
        messages.error(request, f"Error al restaurar backup: {str(e)}")
    
    return redirect("backup_list")


def _restore_json_backup(backup_path):
    """Restaurar backup en formato JSON"""
    from django.core import serializers
    from django.apps import apps
    from django.db import transaction
    
    with open(backup_path, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    with transaction.atomic():
        # Limpiar todas las tablas (en orden inverso por dependencias)
        for app_config in reversed(apps.get_app_configs()):
            for model in reversed(app_config.get_models()):
                try:
                    model.objects.all().delete()
                except Exception as e:
                    print(f"Error limpiando {model}: {e}")
        
        # Restaurar datos
        for item in backup_data:
            try:
                app_label = item['app']
                model_name = item['model']
                model = apps.get_model(app_label, model_name)
                
                for obj_data in item['data']:
                    obj = serializers.deserialize('json', json.dumps([obj_data]))
                    for deserialized_obj in obj:
                        deserialized_obj.save()
            except Exception as e:
                print(f"Error restaurando {item.get('app')}.{item.get('model')}: {e}")
                continue


def _restore_sql_backup(backup_path):
    """Restaurar backup SQL"""
    db = get_db_settings()
    
    # Usar psycopg2 directamente para mayor control
    conn = psycopg2.connect(
        host=db['HOST'],
        port=db['PORT'],
        user=db['USER'],
        password=db['PASSWORD'],
        database=db['NAME']
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cursor:
            # Leer y ejecutar el archivo SQL
            with open(backup_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Ejecutar en transacción
            conn.autocommit = False
            try:
                cursor.execute(sql_content)
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.autocommit = True
                
    finally:
        conn.close()


# ======================================================
# ELIMINAR BACKUP
# ======================================================
@csrf_exempt
def delete_backup(request, filename):
    if request.method == "POST":
        backup_path = settings.BACKUP_DIR / filename
        if backup_path.exists():
            try:
                backup_path.unlink()
                messages.success(request, f"Backup eliminado: {filename}")
            except Exception as e:
                messages.error(request, f"Error al eliminar: {str(e)}")
        else:
            messages.error(request, "El archivo no existe.")
    
    return redirect("backup_list")