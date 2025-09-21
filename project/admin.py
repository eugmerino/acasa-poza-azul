from django.contrib import admin
from .models import Project, Community, Partner, Directive
from django.contrib.auth.admin import UserAdmin

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "connection_price", "absence_fine")
    search_fields = ("title",)

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "project")
    search_fields = ("name",)
    list_filter = ("project",)

@admin.register(Partner)
class PartnerAdmin(UserAdmin):
    model = Partner
    list_display = ("username", "first_name", "last_name", "dui", "tel", "community", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "dui", "tel")
    list_filter = ("community", "is_active", "is_staff", "is_superuser")

    fieldsets = UserAdmin.fieldsets + (
        ("Información adicional", {
            "fields": ("community", "dui", "tel", "foto")
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Información adicional", {
            "fields": ("community", "dui", "tel", "foto")
        }),
    )

@admin.register(Directive)
class DirectiveAdmin(admin.ModelAdmin):
    list_display = ("partner", "role", "isActive", "start_date", "end_date")
    list_filter = ("role", "isActive", "start_date", "end_date")
    search_fields = (
        "partner__first_name",
        "partner__last_name",
        "partner__username",
        "role",
    )

