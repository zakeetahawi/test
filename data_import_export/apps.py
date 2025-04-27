from django.apps import AppConfig


class DataImportExportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_import_export'
    verbose_name = 'استيراد وتصدير البيانات'

    def ready(self):
        # Import and register template tags
        from django.template.defaulttags import register
        import data_import_export.templatetags.custom_filters
