"""
تسجيل النماذج في واجهة الإدارة
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Database, Backup

@admin.register(Database)
class DatabaseAdmin(admin.ModelAdmin):
    """إدارة قواعد البيانات"""

    list_display = ('name', 'db_type', 'is_active', 'created_at')
    list_filter = ('db_type', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'db_type', 'is_active')
        }),
        (_('معلومات الاتصال'), {
            'fields': ('connection_info',),
            'classes': ('collapse',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    """إدارة النسخ الاحتياطية"""

    list_display = ('name', 'database', 'size_display', 'created_at', 'created_by')
    list_filter = ('database', 'created_at')
    search_fields = ('name', 'database__name')
    readonly_fields = ('size', 'created_at', 'created_by')
    fieldsets = (
        (None, {
            'fields': ('name', 'database', 'file_path')
        }),
        (_('معلومات النظام'), {
            'fields': ('size', 'created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
