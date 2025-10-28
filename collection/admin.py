from django.contrib import admin
from .models import Fee, Range, Reading

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

@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "connection", "fee", "date_reading", "meter_reading", "isPaid")
    search_fields = ("connection__id", "fee__short_description")
    list_filter = ("isPaid",)