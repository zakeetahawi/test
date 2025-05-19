"""
إعداد قاعدة بيانات Railway تلقائياً
"""

import os
import logging
from django.conf import settings
from django.db import connections
from django.contrib.auth import get_user_model

from data_management.modules.db_manager.models import DatabaseConfig

logger = logging.getLogger(__name__)

def setup_railway_database():
    """
    إعداد قاعدة بيانات Railway تلقائياً إذا كنا في بيئة Railway
    """
    # التحقق مما إذا كنا في بيئة Railway
    is_railway = 'POSTGRES_PASSWORD' in os.environ

    if not is_railway:
        logger.info("لسنا في بيئة Railway، تخطي إعداد قاعدة البيانات التلقائي")
        return

    print("تم اكتشاف بيئة Railway في railway_db_setup.py، جاري إعداد قاعدة البيانات...")

    logger.info("تم اكتشاف بيئة Railway، جاري إعداد قاعدة البيانات تلقائياً...")

    # الحصول على بيانات الاتصال من متغيرات البيئة
    db_host = os.environ.get('RAILWAY_PRIVATE_DOMAIN', 'localhost')
    db_port = os.environ.get('PGPORT', '5432')
    db_name = os.environ.get('POSTGRES_DB', 'railway')
    db_user = os.environ.get('POSTGRES_USER', 'postgres')
    db_password = os.environ.get('POSTGRES_PASSWORD', '')

    # طباعة معلومات الاتصال للتشخيص
    print(f"معلومات الاتصال بقاعدة البيانات:")
    print(f"Host: {db_host}")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")

    # التحقق من وجود قاعدة بيانات Railway في النظام
    railway_db = DatabaseConfig.objects.filter(
        host=db_host,
        database_name=db_name
    ).first()

    if railway_db:
        logger.info(f"قاعدة بيانات Railway موجودة بالفعل: {railway_db.name}")

        # تحديث بيانات الاتصال إذا تغيرت
        if (railway_db.port != db_port or
            railway_db.username != db_user or
            railway_db.password != db_password):

            railway_db.port = db_port
            railway_db.username = db_user
            railway_db.password = db_password
            railway_db.save()

            logger.info("تم تحديث بيانات الاتصال بقاعدة بيانات Railway")

        # تنشيط قاعدة البيانات إذا لم تكن نشطة
        if not railway_db.is_active:
            # إلغاء تنشيط جميع قواعد البيانات الأخرى
            DatabaseConfig.objects.all().update(is_active=False)

            # تنشيط قاعدة بيانات Railway
            railway_db.is_active = True
            railway_db.save()

            logger.info("تم تنشيط قاعدة بيانات Railway")
    else:
        # إنشاء قاعدة بيانات Railway جديدة
        railway_db = DatabaseConfig(
            name="Railway PostgreSQL",
            db_type="postgresql",
            host=db_host,
            port=db_port,
            username=db_user,
            password=db_password,
            database_name=db_name,
            is_active=True,
            is_default=True
        )
        railway_db.save()

        logger.info("تم إنشاء قاعدة بيانات Railway جديدة")

    # التحقق من وجود مستخدم مدير
    User = get_user_model()
    if User.objects.count() == 0:
        # إنشاء مستخدم مدير افتراضي
        admin_user = User.objects.create_superuser(
            username="admin",
            password="admin",
            email="admin@example.com"
        )
        logger.info("تم إنشاء مستخدم مدير افتراضي (admin/admin)")

    # اختبار الاتصال بقاعدة البيانات
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                logger.info("تم الاتصال بقاعدة بيانات Railway بنجاح")

                # تنفيذ الترحيلات
                logger.info("جاري تنفيذ الترحيلات...")
                try:
                    from django.core.management import call_command
                    call_command('migrate', '--noinput')
                    logger.info("تم تنفيذ الترحيلات بنجاح")
                except Exception as migrate_error:
                    logger.error(f"حدث خطأ أثناء تنفيذ الترحيلات: {str(migrate_error)}")
            else:
                logger.error("فشل اختبار الاتصال بقاعدة بيانات Railway")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء الاتصال بقاعدة بيانات Railway: {str(e)}")
