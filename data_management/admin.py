from django.contrib import admin
from django.utils.translation import gettext_lazy as _

# استيراد النماذج من الوحدات الفرعية
from .modules.backup.models import BackupHistory, GoogleSheetsConfig, SyncLog
from .modules.db_manager.models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken
from .modules.import_export.models import ImportExportLog, ImportTemplate

# تسجيل نماذج وحدة النسخ الاحتياطي
@admin.register(BackupHistory)
class BackupHistoryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'backup_type', 'file_name', 'status', 'created_by')
    list_filter = ('backup_type', 'status', 'is_compressed', 'is_encrypted')
    search_fields = ('file_name', 'backup_location')
    readonly_fields = ('timestamp', 'file_size', 'file_checksum')
    date_hierarchy = 'timestamp'

@admin.register(GoogleSheetsConfig)
class GoogleSheetsConfigAdmin(admin.ModelAdmin):
    list_display = ('sheet_id', 'is_active', 'auto_sync', 'last_sync')
    list_filter = ('is_active', 'auto_sync', 'sync_customers', 'sync_products', 'sync_orders')
    fieldsets = (
        (_('إعدادات أساسية'), {
            'fields': ('sheet_id', 'credentials_file', 'is_active')
        }),
        (_('إعدادات المزامنة'), {
            'fields': ('sync_customers', 'sync_products', 'sync_orders', 'sync_inventory',
                      'sync_inspections', 'sync_installations', 'sync_company_info')
        }),
        (_('جدولة المزامنة'), {
            'fields': ('auto_sync', 'sync_interval', 'last_sync')
        }),
    )
    readonly_fields = ('last_sync',)

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'config', 'status', 'records_synced')
    list_filter = ('status', 'config')
    search_fields = ('errors',)
    readonly_fields = ('timestamp', 'records_synced')
    date_hierarchy = 'timestamp'

# تسجيل نماذج وحدة إدارة قواعد البيانات
@admin.register(DatabaseConfig)
class DatabaseConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'db_type', 'host', 'is_active', 'is_default')
    list_filter = ('db_type', 'is_active', 'is_default')
    search_fields = ('name', 'host', 'database_name')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'db_type', 'is_active', 'is_default')
        }),
        (_('معلومات الاتصال'), {
            'fields': ('host', 'port', 'username', 'password', 'database_name'),
            'classes': ('collapse',)
        }),
        (_('معلومات إضافية'), {
            'fields': ('connection_string',),
            'classes': ('collapse',)
        }),
    )

@admin.register(DatabaseBackup)
class DatabaseBackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'backup_type', 'database_config', 'created_at', 'created_by')
    list_filter = ('backup_type', 'database_config', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'size')
    date_hierarchy = 'created_at'

@admin.register(DatabaseImport)
class DatabaseImportAdmin(admin.ModelAdmin):
    list_display = ('id', 'database_config', 'status', 'created_at', 'created_by')
    list_filter = ('status', 'database_config', 'clear_data')
    search_fields = ('log',)
    readonly_fields = ('created_at', 'completed_at')
    date_hierarchy = 'created_at'

@admin.register(SetupToken)
class SetupTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'is_used', 'created_at', 'expires_at', 'is_valid')
    list_filter = ('is_used',)
    readonly_fields = ('token', 'created_at')
    date_hierarchy = 'created_at'

# تسجيل نماذج وحدة استيراد وتصدير البيانات
@admin.register(ImportExportLog)
class ImportExportLogAdmin(admin.ModelAdmin):
    list_display = ('operation_type', 'model_name', 'file_name', 'status', 'records_count', 'created_at')
    list_filter = ('operation_type', 'status', 'model_name')
    search_fields = ('file_name', 'model_name')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'records_count', 'success_count', 'error_count')
    date_hierarchy = 'created_at'

@admin.register(ImportTemplate)
class ImportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'model_name')
    search_fields = ('name', 'description', 'model_name')
    readonly_fields = ('created_at', 'updated_at')
