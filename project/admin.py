from django.contrib import admin
from .models import Project, community, Fee, Range

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "connection_price", "absence_fine")
    search_fields = ("title",)

@admin.register(community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "project")
    search_fields = ("name",)
    list_filter = ("project",)

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ("short_description", "approval_date", "isActive")
    search_fields = ("short_description",)
    list_filter = ("isActive",)

@admin.register(Range)
class RangeAdmin(admin.ModelAdmin):
    list_display = ("fee", "min_meter", "max_meter", "fixed_amount", "amount_meter")
    search_fields = ("fee__short_description",)
    list_filter = ("fee",)

