from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import sys


class DataManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_management'
    verbose_name = _('إدارة البيانات')

    def ready(self):
        """تنفيذ الإعدادات عند تحميل التطبيق"""
        # استيراد إشارات التطبيق
        try:
            import data_management.signals
        except ImportError:
            # تجاهل الخطأ إذا لم يكن ملف الإشارات موجودًا
            pass

        # نتأكد من عدم تشغيل المجدول أثناء المهام الإدارية لتفادي أخطاء قاعدة البيانات
        if 'runserver' in sys.argv and 'makemigrations' not in sys.argv and 'migrate' not in sys.argv and 'shell' not in sys.argv:
            try:
                from .scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                print(f"خطأ في تشغيل المجدول: {str(e)}")
                pass

        # إنشاء مستخدم افتراضي إذا لم يكن هناك مستخدمين
        self.create_default_user()

    def create_default_user(self):
        """إنشاء مستخدم افتراضي إذا لم يكن هناك مستخدمين"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # التحقق من وجود مستخدمين
            if User.objects.count() == 0:
                # إنشاء مستخدم افتراضي
                User.objects.create_superuser(
                    username='admin',
                    password='admin',
                    email='admin@example.com'
                )
                print("تم إنشاء مستخدم افتراضي (admin/admin)")
        except Exception as e:
            print(f"خطأ في إنشاء المستخدم الافتراضي: {str(e)}")
            pass
