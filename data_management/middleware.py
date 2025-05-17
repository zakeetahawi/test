"""
وسيط إدارة قواعد البيانات
"""

import logging
from django.db import connections
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class DatabaseSwitchMiddleware:
    """
    وسيط لتبديل قاعدة البيانات النشطة

    يقوم هذا الوسيط بتحميل إعدادات قاعدة البيانات النشطة من قاعدة البيانات الافتراضية
    وتطبيقها على اتصال قاعدة البيانات الافتراضي.
    """

    def __init__(self, get_response):
        """تهيئة الوسيط"""
        self.get_response = get_response

    def __call__(self, request):
        """
        معالجة الطلب

        يتم استدعاء هذه الدالة لكل طلب HTTP
        """
        # تحقق مما إذا كان المستخدم مسجل الدخول ومدير
        if request.user.is_authenticated and request.user.is_superuser:
            # تحقق مما إذا كان هناك طلب لتبديل قاعدة البيانات
            if 'switch_db' in request.GET:
                db_id = request.GET.get('switch_db')
                self.switch_database(db_id)

            # تحقق مما إذا كان هناك طلب لإعادة تحميل إعدادات قاعدة البيانات
            elif 'reload_db_settings' in request.GET:
                self.reload_database_settings()

        # استمر في معالجة الطلب
        response = self.get_response(request)
        return response

    def switch_database(self, db_id):
        """
        تبديل قاعدة البيانات النشطة

        Args:
            db_id: معرف قاعدة البيانات
        """
        try:
            # استيراد نموذج قاعدة البيانات
            from data_management.modules.db_manager.models import DatabaseConfig

            # الحصول على قاعدة البيانات
            database = DatabaseConfig.objects.get(id=db_id)

            # تعيين قاعدة البيانات كنشطة
            DatabaseConfig.objects.all().update(is_active=False)
            database.is_active = True
            database.save()

            # تحديث إعدادات قاعدة البيانات
            self.update_database_settings(database)

            # تنظيف ذاكرة التخزين المؤقت
            cache.clear()

            logger.info(f"تم تبديل قاعدة البيانات النشطة إلى {database.name}")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء تبديل قاعدة البيانات: {str(e)}")

    def reload_database_settings(self):
        """إعادة تحميل إعدادات قاعدة البيانات النشطة"""
        try:
            # استيراد نموذج قاعدة البيانات
            from data_management.modules.db_manager.models import DatabaseConfig

            # الحصول على قاعدة البيانات النشطة
            database = DatabaseConfig.objects.filter(is_active=True).first()

            if database:
                # تحديث إعدادات قاعدة البيانات
                self.update_database_settings(database)

                # تنظيف ذاكرة التخزين المؤقت
                cache.clear()

                logger.info(f"تم إعادة تحميل إعدادات قاعدة البيانات النشطة {database.name}")
            else:
                logger.warning("لا توجد قاعدة بيانات نشطة")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء إعادة تحميل إعدادات قاعدة البيانات: {str(e)}")

    def update_database_settings(self, database):
        """
        تحديث إعدادات قاعدة البيانات

        Args:
            database: كائن قاعدة البيانات
        """
        # الحصول على الإعدادات الحالية
        current_settings = settings.DATABASES.get('default', {})

        # إنشاء إعدادات الاتصال
        db_settings = {
            'ENGINE': f"django.db.backends.{database.db_type}",
            'NAME': database.database_name,
            'USER': database.username,
            'PASSWORD': database.password,
            'HOST': database.host,
            'PORT': database.port,
            # إضافة إعدادات إضافية مهمة
            'ATOMIC_REQUESTS': current_settings.get('ATOMIC_REQUESTS', False),
            'AUTOCOMMIT': current_settings.get('AUTOCOMMIT', True),
            'CONN_MAX_AGE': current_settings.get('CONN_MAX_AGE', 0),
            'OPTIONS': current_settings.get('OPTIONS', {}),
            'TIME_ZONE': current_settings.get('TIME_ZONE', None),
            'TEST': current_settings.get('TEST', {}),
        }

        # تحديث إعدادات قاعدة البيانات
        settings.DATABASES['default'] = db_settings

        # إغلاق الاتصال الحالي
        connections.close_all()

        logger.info(f"تم تحديث إعدادات قاعدة البيانات إلى {database.name}")
