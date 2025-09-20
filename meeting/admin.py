from django.contrib import admin
from .models import Meeting, Attendance

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "start_time", "end_time", "isActive")
    search_fields = ("title",)
    list_filter = ("date", "isActive")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("meeting", "partner")
    list_filter = ("meeting", "partner")
    search_fields = (
        "meeting__title",
        "partner__username",
        "partner__first_name",
        "partner__last_name",
    )