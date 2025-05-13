from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DbManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'db_manager'
    verbose_name = _('إدارة قواعد البيانات')

    def ready(self):
        """تنفيذ الإعدادات عند تحميل التطبيق"""
        # استيراد إشارات التطبيق
        try:
            import db_manager.signals
        except ImportError:
            # تجاهل الخطأ إذا لم يكن ملف الإشارات موجودًا
            pass

        # إنشاء مستخدم افتراضي إذا لم يكن هناك مستخدمين
        self.create_default_user()

    def create_default_user(self):
        """إنشاء مستخدم افتراضي إذا لم يكن هناك مستخدمين"""
        import os
        import sys

        # تجاهل إنشاء المستخدم الافتراضي في بعض الحالات
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv or 'collectstatic' in sys.argv:
            return

        # استخدام متغير بيئي للتحكم في إنشاء المستخدم الافتراضي
        if os.environ.get('DISABLE_DEFAULT_USER', '').lower() == 'true':
            return

        try:
            from django.contrib.auth import get_user_model
            from django.db import transaction

            User = get_user_model()

            # التحقق من وجود مستخدمين في النظام
            if User.objects.count() == 0:
                with transaction.atomic():
                    # إنشاء مستخدم افتراضي
                    User.objects.create_superuser(
                        username='admin',
                        email='admin@example.com',
                        password='admin'
                    )
                    print("تم إنشاء مستخدم افتراضي (admin/admin)")
        except Exception as e:
            # تجاهل الأخطاء أثناء إنشاء المستخدم الافتراضي
            print(f"حدث خطأ أثناء إنشاء المستخدم الافتراضي: {str(e)}")
