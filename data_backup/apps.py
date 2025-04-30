from django.apps import AppConfig
import sys

class DataBackupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_backup'
    verbose_name = 'مزامنة البيانات مع Google Sheets'

    def ready(self):
        """تشغيل أي عمليات عند بدء تشغيل التطبيق"""
        # نتأكد من عدم تشغيل المجدول أثناء المهام الإدارية لتفادي أخطاء قاعدة البيانات
        if 'runserver' in sys.argv and 'makemigrations' not in sys.argv and 'migrate' not in sys.argv and 'shell' not in sys.argv:
            try:
                from .scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                print(f"خطأ في تشغيل المجدول: {str(e)}")
                pass
