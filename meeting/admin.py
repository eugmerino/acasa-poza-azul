from django.contrib import admin
from .models import Meeting

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "start_time", "end_time", "isActive")
    search_fields = ("title",)
    list_filter = ("date", "isActive")
