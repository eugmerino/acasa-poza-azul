from django.urls import path
from .views import (
    backups_list,
    generate_backup,
    restore_backup,
    download_backup,
)

urlpatterns = [
    path("", backups_list, name="backup_list"),
    path("generate/", generate_backup, name="generate_backup"),
    path("restore/<str:filename>/", restore_backup, name="restore_backup"),
    path("download/<str:filename>/", download_backup, name="download_backup"),
]
