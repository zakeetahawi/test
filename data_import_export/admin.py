from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import messages
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
import pandas as pd
import datetime

from .models import ImportExportLog, ImportTemplate
from .utils import generate_multi_sheet_template, process_multi_sheet_import, generate_multi_sheet_export

@admin.register(ImportExportLog)
class ImportExportLogAdmin(admin.ModelAdmin):
    list_display = ('operation_type', 'model_name', 'file_name', 'status', 'records_count', 'success_count', 'error_count', 'created_at')
    list_filter = ('operation_type', 'status', 'created_at')
    search_fields = ('file_name', 'model_name')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'created_by')
    
    fieldsets = (
        (_('معلومات العملية'), {
            'fields': ('operation_type', 'model_name', 'file', 'file_name')
        }),
        (_('الحالة'), {
            'fields': ('status', 'records_count', 'success_count', 'error_count')
        }),
        (_('تفاصيل الأخطاء'), {
            'fields': ('error_details',),
            'classes': ('collapse',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

class AdminMultiSheetImportExportMixin:
    """
    Mixin for adding import/export functionality to admin
    """
    change_list_template = 'admin/model_change_list.html'
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import/', self.admin_site.admin_view(self.import_view), name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_import'),
            path('export/', self.admin_site.admin_view(self.export_view), name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_export'),
        ]
        return my_urls + urls
    
    def import_view(self, request):
        """
        View for importing data
        """
        if request.method == 'POST':
            # Check if file was uploaded
            if 'file' not in request.FILES:
                self.message_user(request, _('Please select a file to import.'), level=messages.ERROR)
                return redirect('.')
            
            # Get the file
            file = request.FILES['file']
            
            # Create import log
            import_log = ImportExportLog(
                operation_type='import',
                model_name=f'{self.model._meta.app_label}.{self.model._meta.model_name}',
                file_name=file.name,
                file=file,
                status='processing',
                created_by=request.user
            )
            import_log.save()
            
            try:
                # Process the file
                success_count, error_count, error_details = process_multi_sheet_import(import_log.file.path, import_log)
                
                # Update import log
                import_log.success_count = success_count
                import_log.error_count = error_count
                import_log.error_details = '\n'.join(error_details)
                import_log.status = 'completed' if error_count == 0 else 'failed'
                import_log.completed_at = timezone.now()
                import_log.save()
                
                # Show message
                if success_count > 0:
                    self.message_user(request, _(f'Successfully imported {success_count} records.'), level=messages.SUCCESS)
                
                if error_count > 0:
                    self.message_user(request, _(f'Failed to import {error_count} records. See import log for details.'), level=messages.WARNING)
            
            except Exception as e:
                import_log.status = 'failed'
                import_log.error_details = str(e)
                import_log.completed_at = timezone.now()
                import_log.save()
                
                self.message_user(request, _(f'Error importing data: {str(e)}'), level=messages.ERROR)
            
            return redirect('.')
        
        # Get import templates
        templates = ImportTemplate.objects.filter(
            model_name=f'{self.model._meta.app_label}.{self.model._meta.model_name}',
            is_active=True
        )
        
        # Render the form
        context = {
            'title': _(f'Import {self.model._meta.verbose_name_plural}'),
            'templates': templates,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        
        return TemplateResponse(request, 'admin/import_form.html', context)
    
    def export_view(self, request):
        """
        View for exporting data
        """
        # Get the queryset
        queryset = self.get_queryset(request)
        
        # Create export log
        export_log = ImportExportLog(
            operation_type='export',
            model_name=f'{self.model._meta.app_label}.{self.model._meta.model_name}',
            file_name=f'{self.model._meta.model_name}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            status='processing',
            records_count=queryset.count(),
            created_by=request.user
        )
        export_log.save()
        
        try:
            # Generate the Excel file
            output = generate_multi_sheet_export([f'{self.model._meta.app_label}.{self.model._meta.model_name}'])
            
            # Update export log
            export_log.status = 'completed'
            export_log.success_count = queryset.count()
            export_log.completed_at = timezone.now()
            export_log.save()
            
            # Create response
            response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{export_log.file_name}"'
            
            return response
        
        except Exception as e:
            export_log.status = 'failed'
            export_log.error_details = str(e)
            export_log.completed_at = timezone.now()
            export_log.save()
            
            self.message_user(request, _(f'Error exporting data: {str(e)}'), level=messages.ERROR)
            
            return redirect('.')
    
    def changelist_view(self, request, extra_context=None):
        """
        Override changelist view to add import/export buttons
        """
        extra_context = extra_context or {}
        extra_context['import_url'] = f'{self.model._meta.app_label}_{self.model._meta.model_name}_import'
        extra_context['export_url'] = f'{self.model._meta.app_label}_{self.model._meta.model_name}_export'
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(ImportTemplate)
class ImportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_name', 'is_active', 'created_at')
    list_filter = ('model_name', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('معلومات القالب'), {
            'fields': ('name', 'description', 'model_name', 'file', 'is_active')
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
