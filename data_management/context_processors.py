"""
معالجات السياق لتطبيق إدارة البيانات
"""

def data_management_urls(request):
    """
    إضافة عناوين URL الخاصة بتطبيق إدارة البيانات إلى سياق القالب
    """
    return {
        # عناوين URL الرئيسية
        'index': 'data_management:index',
        'dashboard': 'data_management:dashboard',

        # عناوين URL لإدارة قواعد البيانات
        'db_export': 'data_management:db_export',
        'db_import': 'data_management:db_import',

        # عناوين URL لمزامنة غوغل
        'google_sync': 'data_management:google_sync',
        'google_sheets_config': 'data_management:google_sheets_config',
        'google_sheets_sync': 'data_management:google_sheets_sync',
        'gdrive_config': 'data_management:gdrive_config',
        'backup_to_gdrive': 'data_management:backup_to_gdrive',
        'sync_logs': 'data_management:sync_logs',
        'sync_log_detail': 'data_management:sync_log_detail',

        # عناوين URL لاستيراد وتصدير إكسل
        'excel_dashboard': 'data_management:excel_dashboard',
        'excel_import': 'data_management:excel_import',
        'excel_export': 'data_management:excel_export',
        'excel_import_logs': 'data_management:excel_import_logs',
        'excel_export_logs': 'data_management:excel_export_logs',

        # جدولة النسخ الاحتياطي
        'schedule_backup': 'data_management:schedule_backup',
    }
