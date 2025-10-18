from django.contrib import admin
from .models import Transaction, Payment


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('concept', 'type', 'amount', 'project', 'date')
    list_filter = ('type', 'date', 'project')
    search_fields = ('concept',)
    ordering = ('-date',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('connection', 'amount', 'date_pay')
    list_filter = ('date_pay',)
    search_fields = ('connection__description',)
    ordering = ('-date_pay',)
