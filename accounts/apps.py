from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Import signal handlers
        from . import signals  # noqa

        # Register post_migrate signal to create departments
        # استخدام وظيفة مساعدة لتجنب الوصول إلى قاعدة البيانات مباشرة
        post_migrate.connect(self._post_migrate_callback, sender=self)

    def _post_migrate_callback(self, *args, **kwargs):
        """
        وظيفة مساعدة لتجنب الوصول إلى قاعدة البيانات أثناء تهيئة التطبيق
        """
        # استخدام استدعاء متأخر لإنشاء الأقسام
        from django.core.management import call_command

        # استخدام أمر الإدارة بدلاً من الوصول المباشر إلى قاعدة البيانات
        call_command('create_core_departments')
        # تم تعطيل create_departments لمنع إنشاء الإدارات والوحدات الإضافية
        # call_command('create_departments')
