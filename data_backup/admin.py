from django.contrib import admin
from .models import GoogleSheetsConfig, SyncLog

@admin.register(GoogleSheetsConfig)
class GoogleSheetsConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_active', 'auto_sync_enabled', 'sync_interval_minutes', 'last_sync')
    list_filter = ('is_active', 'auto_sync_enabled')
    fieldsets = (
        ('إعدادات الاتصال', {
            'fields': ('spreadsheet_id', 'credentials_file', 'is_active')
        }),
        ('إعدادات المزامنة التلقائية', {
            'fields': ('auto_sync_enabled', 'sync_interval_minutes', 'last_sync')
        }),
        ('البيانات للمزامنة', {
            'fields': ('sync_customers', 'sync_orders', 'sync_products', 'sync_inspections', 'sync_installations')
        }),
    )
    readonly_fields = ('last_sync',)

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'status', 'records_synced', 'triggered_by')
    list_filter = ('status', 'timestamp')
    readonly_fields = ('timestamp', 'status', 'details', 'records_synced', 'triggered_by')
