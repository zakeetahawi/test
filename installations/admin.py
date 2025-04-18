from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Installation, TransportRequest

@admin.register(Installation)
class InstallationAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'invoice_number', 'status', 'scheduled_date', 'payment_verified', 'branch')
    list_filter = ('status', 'payment_verified', 'branch', 'created_at')
    search_fields = ('customer__name', 'invoice_number', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('order', 'customer', 'branch', 'invoice_number')
        }),
        (_('حالة التركيب'), {
            'fields': ('status', 'payment_verified', 'scheduled_date', 'technician')
        }),
        (_('ملاحظات'), {
            'fields': ('notes',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TransportRequest)
class TransportRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'installation', 'status', 'scheduled_date', 'driver')
    list_filter = ('status', 'created_at')
    search_fields = ('installation__customer__name', 'from_location', 'to_location', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('installation', 'from_location', 'to_location')
        }),
        (_('حالة النقل'), {
            'fields': ('status', 'scheduled_date', 'driver')
        }),
        (_('ملاحظات'), {
            'fields': ('notes',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
