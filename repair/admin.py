from django.contrib import admin
from .models import Repair

@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    list_display = (
        'report_title',
        'community',
        'plumber',
        'report_date',
        'repair_date',
        'payment_amount',
        'is_paid',
    )
    list_filter = (
        'community',
        'plumber',
        'is_paid',
        'report_date',
        'repair_date',
    )
    search_fields = (
        'report_title',
        'community__name',
        'plumber__first_name',
        'plumber__last_name',
        'report_description',
        'repair_description',
    )
    readonly_fields = ('report_date',)
    
    fieldsets = (
        ('Información del Reporte', {
            'fields': (
                'community',
                'report_title',
                'report_date',
                'report_description',
                'report_photo',
            ),
        }),
        ('Información de la Reparación', {
            'fields': (
                'repair_date',
                'plumber',
                'repair_description',
                'repair_photo',
            ),
        }),
        ('Pago', {
            'fields': (
                'payment_amount',
                'payment_date',
                'is_paid',
            ),
        }),
    )


