"""
أمر إدارة لإعداد قاعدة بيانات Railway تلقائياً
"""

import os
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from data_management.modules.db_manager.models import DatabaseConfig
from data_management.railway_db_setup import setup_railway_database

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'إعداد قاعدة بيانات Railway تلقائياً'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='إجبار إعادة إنشاء قاعدة البيانات حتى لو كانت موجودة',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        self.stdout.write(self.style.SUCCESS('بدء إعداد قاعدة بيانات Railway...'))

        # التحقق مما إذا كنا في بيئة Railway
        is_railway = os.environ.get('RAILWAY_ENVIRONMENT') == 'production' or 'railway' in os.environ.get('PGHOST', '')

        if not is_railway:
            self.stdout.write(self.style.WARNING('لسنا في بيئة Railway، هل تريد المتابعة؟ (y/n)'))
            answer = input().lower()
            if answer != 'y':
                self.stdout.write(self.style.ERROR('تم إلغاء العملية.'))
                return

        # الحصول على بيانات الاتصال من متغيرات البيئة
        db_host = os.environ.get('PGHOST', 'postgres.railway.internal')
        db_port = os.environ.get('PGPORT', '5432')
        db_name = os.environ.get('PGDATABASE', 'railway')
        db_user = os.environ.get('PGUSER', 'postgres')
        db_password = os.environ.get('PGPASSWORD') or os.environ.get('POSTGRES_PASSWORD', '')

        self.stdout.write(f'بيانات الاتصال:')
        self.stdout.write(f'  المضيف: {db_host}')
        self.stdout.write(f'  المنفذ: {db_port}')
        self.stdout.write(f'  اسم قاعدة البيانات: {db_name}')
        self.stdout.write(f'  اسم المستخدم: {db_user}')

        # التحقق من وجود قاعدة بيانات Railway في النظام
        railway_db = DatabaseConfig.objects.filter(
            host=db_host,
            database_name=db_name
        ).first()

        if railway_db and not force:
            self.stdout.write(self.style.SUCCESS(f'قاعدة بيانات Railway موجودة بالفعل: {railway_db.name}'))

            # تحديث بيانات الاتصال إذا تغيرت
            if (railway_db.port != db_port or
                railway_db.username != db_user or
                railway_db.password != db_password):

                railway_db.port = db_port
                railway_db.username = db_user
                railway_db.password = db_password
                railway_db.save()

                self.stdout.write(self.style.SUCCESS('تم تحديث بيانات الاتصال بقاعدة بيانات Railway'))

            # تنشيط قاعدة البيانات إذا لم تكن نشطة
            if not railway_db.is_active:
                # إلغاء تنشيط جميع قواعد البيانات الأخرى
                DatabaseConfig.objects.all().update(is_active=False)

                # تنشيط قاعدة بيانات Railway
                railway_db.is_active = True
                railway_db.save()

                self.stdout.write(self.style.SUCCESS('تم تنشيط قاعدة بيانات Railway'))
        else:
            # إنشاء قاعدة بيانات Railway جديدة
            if railway_db and force:
                self.stdout.write(self.style.WARNING(f'حذف قاعدة البيانات الموجودة: {railway_db.name}'))
                railway_db.delete()

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

            self.stdout.write(self.style.SUCCESS('تم إنشاء قاعدة بيانات Railway جديدة'))

        # التحقق من وجود مستخدم مدير
        User = get_user_model()
        if User.objects.count() == 0:
            # إنشاء مستخدم مدير افتراضي
            admin_user = User.objects.create_superuser(
                username="admin",
                password="admin",
                email="admin@example.com"
            )
            self.stdout.write(self.style.SUCCESS('تم إنشاء مستخدم مدير افتراضي (admin/admin)'))

        # اختبار الاتصال بقاعدة البيانات
        try:
            from django.db import connections
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    self.stdout.write(self.style.SUCCESS('تم الاتصال بقاعدة بيانات Railway بنجاح'))

                    # تنفيذ الترحيلات
                    self.stdout.write('جاري تنفيذ الترحيلات...')
                    try:
                        from django.core.management import call_command
                        call_command('migrate', '--noinput', verbosity=1)
                        self.stdout.write(self.style.SUCCESS('تم تنفيذ الترحيلات بنجاح'))
                    except Exception as migrate_error:
                        self.stdout.write(self.style.ERROR(f'حدث خطأ أثناء تنفيذ الترحيلات: {str(migrate_error)}'))
                else:
                    self.stdout.write(self.style.ERROR('فشل اختبار الاتصال بقاعدة بيانات Railway'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'حدث خطأ أثناء الاتصال بقاعدة بيانات Railway: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('اكتمل إعداد قاعدة بيانات Railway'))
