from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken


@admin.register(DatabaseConfig)
class DatabaseConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'db_type', 'host', 'is_active', 'is_default', 'created_at')
    list_filter = ('db_type', 'is_active', 'is_default')
    search_fields = ('name', 'host', 'database_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'db_type', 'is_active', 'is_default')
        }),
        (_('تفاصيل الاتصال'), {
            'fields': ('host', 'port', 'username', 'password', 'database_name', 'connection_string'),
            'classes': ('collapse',),
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(DatabaseBackup)
class DatabaseBackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'backup_type', 'database_config', 'size_display', 'created_by', 'created_at')
    list_filter = ('backup_type', 'database_config', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('size', 'created_at', 'created_by')

    def size_display(self, obj):
        """عرض حجم الملف بشكل مقروء"""
        if obj.size < 1024:
            return f"{obj.size} بايت"
        elif obj.size < 1024 * 1024:
            return f"{obj.size / 1024:.2f} كيلوبايت"
        elif obj.size < 1024 * 1024 * 1024:
            return f"{obj.size / (1024 * 1024):.2f} ميجابايت"
        else:
            return f"{obj.size / (1024 * 1024 * 1024):.2f} جيجابايت"

    size_display.short_description = _('الحجم')


@admin.register(DatabaseImport)
class DatabaseImportAdmin(admin.ModelAdmin):
    list_display = ('id', 'database_config', 'status', 'created_by', 'created_at', 'completed_at')
    list_filter = ('status', 'database_config', 'created_at')
    readonly_fields = ('created_at', 'completed_at', 'created_by', 'log')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('file', 'database_config', 'status')
        }),
        (_('سجل العملية'), {
            'fields': ('log',),
            'classes': ('collapse',),
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(SetupToken)
class SetupTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'is_valid_display', 'created_at', 'expires_at', 'used_at')
    readonly_fields = ('token', 'created_at')

    def is_valid_display(self, obj):
        """عرض حالة صلاحية الرمز"""
        if obj.is_valid:
            return True
        elif obj.is_used:
            return False
        elif obj.is_expired:
            return False
        return False

    is_valid_display.short_description = _('صالح')
    is_valid_display.boolean = True
