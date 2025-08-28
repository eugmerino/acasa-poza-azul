from django.contrib import admin
from .models import Project, Community

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "connection_price", "absence_fine")
    search_fields = ("title",)

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "project")
    search_fields = ("name",)
    list_filter = ("project",)

