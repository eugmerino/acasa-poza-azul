from django.contrib import admin
from .models import LogEntry

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "action",
        "model_name",
        "object_id",
        "created_at",
    )

    list_filter = (
        "action",
        "model_name",
        "user",
        "created_at",
    )

    search_fields = (
        "description",
        "model_name",
        "object_id",
        "user__name",  # Ajusta si Partner usa otro campo como username/fullname
    )

    readonly_fields = (
        "user",
        "action",
        "model_name",
        "object_id",
        "description",
        "created_at",
    )

    ordering = ("-created_at",)

    # Deshabilitar edición para que actúe como un log real
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
