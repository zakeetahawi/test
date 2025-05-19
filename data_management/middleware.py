"""
وسيط إدارة قواعد البيانات وتتبع الأخطاء
"""

import os
import sys
import json
import traceback
import logging
import threading
import subprocess
from django.db import connections
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

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

            # تنفيذ الترحيلات على قاعدة البيانات الجديدة
            try:
                from django.core.management import call_command
                logger.info("جاري تنفيذ الترحيلات على قاعدة البيانات الجديدة...")
                call_command('migrate', '--noinput')
                logger.info("تم تنفيذ الترحيلات بنجاح")

                # إعادة تشغيل السيرفر (في بيئة التطوير فقط)
                if settings.DEBUG:
                    logger.info("جاري إعادة تشغيل السيرفر...")
                    self._restart_server()
            except Exception as migrate_error:
                logger.error(f"حدث خطأ أثناء تنفيذ الترحيلات: {str(migrate_error)}")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء تبديل قاعدة البيانات: {str(e)}")

    def _restart_server(self):
        """
        إعادة تشغيل السيرفر (في بيئة التطوير فقط)
        """
        try:
            # إنشاء ملف إعادة التشغيل
            restart_file = os.path.join(settings.BASE_DIR, 'restart.txt')
            with open(restart_file, 'w') as f:
                f.write(f"Restart requested at {timezone.now()}")

            # إذا كنا في بيئة التطوير، نحاول إعادة تشغيل السيرفر
            if settings.DEBUG:
                from django.core.management import call_command

                # استخدام أمر إعادة تشغيل السيرفر
                logger.info("جاري تنفيذ أمر إعادة تشغيل السيرفر...")

                # تنفيذ الأمر في خلفية منفصلة
                import threading
                def run_restart_command():
                    try:
                        # استخدام أمر إعادة تشغيل السيرفر
                        call_command('restart_server', delay=3)
                    except Exception as cmd_error:
                        logger.error(f"حدث خطأ أثناء تنفيذ أمر إعادة تشغيل السيرفر: {str(cmd_error)}")

                # تشغيل الأمر في خلفية منفصلة
                threading.Thread(target=run_restart_command).start()

                logger.info("تم طلب إعادة تشغيل السيرفر")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء محاولة إعادة تشغيل السيرفر: {str(e)}")

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


class RailwayDebugMiddleware(MiddlewareMixin):
    """
    وسيط لتتبع الأخطاء في بيئة Railway
    """

    def process_exception(self, request, exception):
        """
        معالجة الاستثناءات وعرض معلومات تفصيلية عنها في بيئة Railway
        """
        # تفعيل وضع تتبع الأخطاء دائمًا في بيئة Railway
        is_railway = 'RAILWAY_ENVIRONMENT' in os.environ or 'railway' in os.environ.get('PGHOST', '')

        if is_railway or settings.DEBUG:
            # تسجيل الخطأ
            logger.error(f"[Railway Exception] {exception}")
            logger.error(traceback.format_exc())

            # إعداد معلومات الخطأ
            exc_info = sys.exc_info()

            # إعداد سياق القالب
            context = {
                'exception_type': exc_info[0].__name__ if exc_info[0] else 'Unknown',
                'exception_value': str(exc_info[1]),
                'exception_traceback': traceback.format_exception(*exc_info),
                'request': request,
                'request_path': request.path,
                'request_method': request.method,
            }

            # جمع معلومات قاعدة البيانات
            db_info = {}
            try:
                db_info = {
                    'ENGINE': settings.DATABASES['default'].get('ENGINE', ''),
                    'NAME': settings.DATABASES['default'].get('NAME', ''),
                    'USER': settings.DATABASES['default'].get('USER', ''),
                    'HOST': settings.DATABASES['default'].get('HOST', ''),
                    'PORT': settings.DATABASES['default'].get('PORT', ''),
                }

                # التحقق من اتصال قاعدة البيانات
                from django.db import connections
                with connections['default'].cursor() as cursor:
                    cursor.execute("SELECT 1")
                    db_info['connection_test'] = "OK"
            except Exception as db_error:
                db_info['connection_error'] = str(db_error)

            # جمع معلومات متغيرات البيئة المتعلقة بقاعدة البيانات
            env_info = {}
            for key in ['PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'RAILWAY_ENVIRONMENT']:
                if key in os.environ:
                    env_info[key] = os.environ[key]

            # عرض معلومات الخطأ كنص عادي
            error_text = f"""
            Railway Debug Error:

            Exception Type: {context['exception_type']}
            Exception Value: {context['exception_value']}

            Traceback:
            {''.join(context['exception_traceback'])}

            Request Path: {context['request_path']}
            Request Method: {context['request_method']}

            Database Info:
            {json.dumps(db_info, indent=4)}

            Environment Variables:
            {json.dumps(env_info, indent=4)}
            """
            return HttpResponse(error_text, content_type='text/plain', status=500)

        # إذا لم يكن وضع تتبع الأخطاء مفعلاً، دع Django يتعامل مع الخطأ
        return None
