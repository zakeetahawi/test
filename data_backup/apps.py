from django.apps import AppConfig


class DataBackupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_backup'
    verbose_name = 'مزامنة البيانات مع Google Sheets'

    def ready(self):
        """تشغيل أي عمليات عند بدء تشغيل التطبيق"""
        pass
