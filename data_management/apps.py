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

        # تأجيل تشغيل المجدول لتجنب الوصول إلى قاعدة البيانات أثناء تهيئة التطبيق
        # سيتم تشغيل المجدول عند الحاجة من خلال طلب HTTP بدلاً من ذلك

        # ملاحظة: تم إزالة إنشاء المستخدم الافتراضي التلقائي لأسباب أمنية
        # استخدم الأمر: python manage.py create_admin_user لإنشاء مستخدم مسؤول عند الحاجة
