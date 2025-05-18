"""
مسارات تطبيق إدارة البيانات
"""

from django.urls import path, include
from . import views

app_name = 'data_management'

urlpatterns = [
    # الصفحة الرئيسية - داشبورد إدارة البيانات
    path('', views.dashboard, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # وحدة النسخ الاحتياطي
    path('backup/', include('data_management.modules.backup.urls')),

    # روابط النسخ الاحتياطي المباشرة
    path('backup/create/', views.create_backup, name='create_backup'),
    path('backup/list/', views.backup_list, name='backup_list'),

    # وحدة إدارة قواعد البيانات
    path('db-manager/', include('data_management.modules.db_manager.urls')),

    # وحدة مزامنة غوغل
    path('google-sync/', views.google_sync_dashboard, name='google_sync'),
    path('google-sync/sheets-config/', views.google_sheets_config, name='google_sheets_config'),
    path('google-sync/sheets-sync/', views.google_sheets_sync, name='google_sheets_sync'),
    path('google-sync/gdrive-config/', views.gdrive_config, name='gdrive_config'),
    path('google-sync/backup-to-gdrive/', views.backup_to_gdrive, name='backup_to_gdrive'),
    path('google-sync/gdrive-backups/', views.gdrive_backups, name='gdrive_backups'),
    path('google-sync/schedule/', views.schedule_sync, name='schedule_sync'),
    path('google-sync/logs/', views.sync_logs, name='sync_logs'),
    path('google-sync/logs/<int:pk>/', views.sync_log_detail, name='sync_log_detail'),

    # وحدة استيراد وتصدير إكسل
    path('excel/', views.excel_dashboard, name='excel_dashboard'),
    path('excel/import/', views.excel_import, name='excel_import'),
    path('excel/export/', views.excel_export, name='excel_export'),
    path('excel/template/', views.excel_template, name='excel_template'),
    path('excel/import-logs/', views.excel_import_logs, name='excel_import_logs'),
    path('excel/export-logs/', views.excel_export_logs, name='excel_export_logs'),

    # جدولة النسخ الاحتياطي
    path('schedule-backup/', views.schedule_backup, name='schedule_backup'),
]
