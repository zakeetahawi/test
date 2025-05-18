"""
خدمات وحدة إدارة قواعد البيانات
"""

import os
import subprocess
import tempfile
import json
import datetime
import uuid
import shutil
import logging
from django.conf import settings
from django.utils import timezone
from django.db import connection, connections
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.crypto import get_random_string

from .models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken

# إعداد المسجل
logger = logging.getLogger(__name__)

class DatabaseService:
    """خدمة إدارة قواعد البيانات"""

    def __init__(self, database_id=None):
        """
        تهيئة الخدمة

        Args:
            database_id: معرف قاعدة البيانات
        """
        if database_id:
            self.database = DatabaseConfig.objects.get(id=database_id)
        else:
            self.database = DatabaseConfig.objects.filter(is_active=True).first()

    def test_connection(self, database_config=None):
        """
        اختبار الاتصال بقاعدة البيانات

        Args:
            database_config: إعدادات قاعدة البيانات

        Returns:
            True إذا نجح الاتصال
        """
        if database_config is None:
            database_config = self.database

        # إنشاء إعدادات الاتصال
        db_settings = {
            'ENGINE': f"django.db.backends.{database_config.db_type}",
            'NAME': database_config.database_name,
            'USER': database_config.username,
            'PASSWORD': database_config.password,
            'HOST': database_config.host,
            'PORT': database_config.port,
        }

        # اختبار الاتصال
        try:
            connections.create_connection(db_settings)
            return True
        except Exception as e:
            return False

    def create_backup(self, database_config=None, backup_type='full', description=None, created_by=None):
        """
        إنشاء نسخة احتياطية لقاعدة البيانات

        Args:
            database_config: إعدادات قاعدة البيانات
            backup_type: نوع النسخة الاحتياطية (full, schema, data)
            description: وصف النسخة الاحتياطية
            created_by: المستخدم الذي أنشأ النسخة الاحتياطية

        Returns:
            كائن DatabaseBackup
        """
        if database_config is None:
            database_config = self.database

        # إنشاء اسم الملف
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{database_config.name}_{backup_type}_{timestamp}.dump"

        # مسار الملف
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'db_backups')
        os.makedirs(backup_dir, exist_ok=True)
        file_path = os.path.join(backup_dir, file_name)

        # إنشاء النسخة الاحتياطية
        if database_config.db_type == 'postgresql':
            self._create_postgresql_backup(database_config, file_path, backup_type)
        elif database_config.db_type == 'mysql':
            self._create_mysql_backup(database_config, file_path, backup_type)
        elif database_config.db_type == 'sqlite':
            self._create_sqlite_backup(database_config, file_path)
        else:
            raise ValueError(f"نوع قاعدة البيانات '{database_config.db_type}' غير مدعوم للنسخ الاحتياطي")

        # حساب حجم الملف
        file_size = os.path.getsize(file_path)

        # إنشاء سجل النسخة الاحتياطية
        backup = DatabaseBackup.objects.create(
            name=f"{database_config.name} {backup_type} Backup - {timestamp}",
            description=description,
            file=os.path.relpath(file_path, settings.MEDIA_ROOT),
            backup_type=backup_type,
            database_config=database_config,
            size=file_size,
            created_by=created_by
        )

        return backup

    def restore_backup(self, backup_id, clear_data=False):
        """
        استعادة نسخة احتياطية

        Args:
            backup_id: معرف النسخة الاحتياطية
            clear_data: هل يتم حذف البيانات القديمة

        Returns:
            True إذا تمت الاستعادة بنجاح
        """
        # الحصول على النسخة الاحتياطية
        backup = DatabaseBackup.objects.get(id=backup_id)

        # التحقق من وجود الملف
        file_path = os.path.join(settings.MEDIA_ROOT, backup.file.name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ملف النسخة الاحتياطية '{file_path}' غير موجود")

        # استعادة النسخة الاحتياطية
        database_config = backup.database_config

        if database_config.db_type == 'postgresql':
            self._restore_postgresql_backup(database_config, file_path, clear_data)
        elif database_config.db_type == 'mysql':
            self._restore_mysql_backup(database_config, file_path, clear_data)
        elif database_config.db_type == 'sqlite':
            self._restore_sqlite_backup(database_config, file_path, clear_data)
        else:
            raise ValueError(f"نوع قاعدة البيانات '{database_config.db_type}' غير مدعوم للاستعادة")

        # تحديث إعدادات قاعدة البيانات في ملف db_settings.json
        try:
            from data_management.db_settings import add_database_settings, set_active_database

            # إنشاء إعدادات قاعدة البيانات
            db_settings = {
                'ENGINE': f"django.db.backends.{database_config.db_type}",
                'NAME': database_config.database_name,
                'USER': database_config.username,
                'PASSWORD': database_config.password,
                'HOST': database_config.host,
                'PORT': database_config.port,
            }

            # إضافة إعدادات قاعدة البيانات
            add_database_settings(database_config.id, db_settings)

            # تعيين قاعدة البيانات النشطة
            set_active_database(database_config.id)

            # تنظيف ذاكرة التخزين المؤقت
            from django.core.cache import cache
            cache.clear()
        except Exception as e:
            logger.error(f"حدث خطأ أثناء تحديث إعدادات قاعدة البيانات: {str(e)}")

        return True

    def import_database(self, file_path, database_config=None, clear_data=False, created_by=None):
        """
        استيراد قاعدة بيانات من ملف

        Args:
            file_path: مسار الملف
            database_config: إعدادات قاعدة البيانات
            clear_data: هل يتم حذف البيانات القديمة
            created_by: المستخدم الذي أنشأ عملية الاستيراد

        Returns:
            كائن DatabaseImport
        """
        if database_config is None:
            database_config = self.database

        # إنشاء سجل الاستيراد
        import_record = DatabaseImport.objects.create(
            file=file_path,
            database_config=database_config,
            status='processing',
            clear_data=clear_data,
            created_by=created_by
        )

        try:
            # تحديد نوع الملف
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.json':
                self._import_json(file_path, database_config, clear_data)
            elif file_ext == '.sql':
                self._import_sql(file_path, database_config, clear_data)
            elif file_ext == '.dump':
                self._import_dump(file_path, database_config, clear_data)
            else:
                raise ValueError(f"نوع الملف '{file_ext}' غير مدعوم للاستيراد")

            # تحديث سجل الاستيراد
            import_record.status = 'completed'
            import_record.completed_at = timezone.now()
            import_record.save()

            return import_record
        except Exception as e:
            # تحديث سجل الاستيراد في حالة الخطأ
            import_record.status = 'failed'
            import_record.log = str(e)
            import_record.save()

            raise

    def create_setup_token(self, expires_in_hours=24):
        """
        إنشاء رمز إعداد

        Args:
            expires_in_hours: عدد ساعات صلاحية الرمز

        Returns:
            كائن SetupToken
        """
        # حساب وقت انتهاء الصلاحية
        expires_at = timezone.now() + datetime.timedelta(hours=expires_in_hours)

        # إنشاء الرمز
        token = SetupToken.objects.create(
            expires_at=expires_at
        )

        return token

    def get_setup_url(self, token):
        """
        الحصول على رابط الإعداد

        Args:
            token: رمز الإعداد

        Returns:
            رابط الإعداد
        """
        return reverse('data_management:db_manager:db_setup_with_token', args=[token.token])

    def _create_postgresql_backup(self, database_config, file_path, backup_type):
        """إنشاء نسخة احتياطية لقاعدة بيانات PostgreSQL"""
        cmd = [
            'pg_dump',
            '--format=custom',
            f"--dbname={database_config.database_name}",
        ]

        if database_config.username:
            cmd.append(f"--username={database_config.username}")

        if database_config.host:
            cmd.append(f"--host={database_config.host}")

        if database_config.port:
            cmd.append(f"--port={database_config.port}")

        if backup_type == 'schema':
            cmd.append('--schema-only')
        elif backup_type == 'data':
            cmd.append('--data-only')

        cmd.append(f"--file={file_path}")

        # تنفيذ الأمر
        env = os.environ.copy()
        if database_config.password:
            env['PGPASSWORD'] = database_config.password

        subprocess.run(cmd, check=True, env=env)

    def _create_mysql_backup(self, database_config, file_path, backup_type):
        """إنشاء نسخة احتياطية لقاعدة بيانات MySQL"""
        cmd = [
            'mysqldump',
            f"--user={database_config.username}",
        ]

        if database_config.password:
            cmd.append(f"--password={database_config.password}")

        if database_config.host:
            cmd.append(f"--host={database_config.host}")

        if database_config.port:
            cmd.append(f"--port={database_config.port}")

        if backup_type == 'schema':
            cmd.append('--no-data')
        elif backup_type == 'data':
            cmd.append('--no-create-info')

        cmd.append(database_config.database_name)

        # تنفيذ الأمر
        with open(file_path, 'w') as f:
            subprocess.run(cmd, check=True, stdout=f)

    def _create_sqlite_backup(self, database_config, file_path):
        """إنشاء نسخة احتياطية لقاعدة بيانات SQLite"""
        # نسخ ملف قاعدة البيانات
        shutil.copy2(database_config.database_name, file_path)

    def _restore_postgresql_backup(self, database_config, file_path, clear_data):
        """استعادة نسخة احتياطية لقاعدة بيانات PostgreSQL"""
        # حذف البيانات القديمة إذا لزم الأمر
        if clear_data:
            self._clear_postgresql_database(database_config)

        # تحقق مما إذا كنا على Railway
        is_railway = "railway" in (database_config.host or "")

        # إنشاء ملف مؤقت للسجل
        log_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log', mode='w+')
        log_file_path = log_file.name
        log_file.close()

        # إعداد بيئة التنفيذ
        env = os.environ.copy()
        if database_config.password:
            env['PGPASSWORD'] = database_config.password

        try:
            # إذا كنا على Railway، نستخدم طريقة مختلفة للاستيراد
            if is_railway:
                logger.info("تم اكتشاف بيئة Railway، استخدام طريقة استيراد خاصة...")

                # استخدام psql بدلاً من pg_restore على Railway
                # أولاً، نقوم بتحويل ملف dump إلى SQL
                sql_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sql')
                sql_file_path = sql_file.name
                sql_file.close()

                # تحويل ملف dump إلى SQL
                convert_cmd = [
                    'pg_restore',
                    '--format=custom',
                    '--file=' + sql_file_path,
                    file_path
                ]

                with open(log_file_path, 'w') as log:
                    process = subprocess.run(
                        convert_cmd,
                        env=env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        check=False
                    )

                # إذا نجح التحويل، نستخدم psql لتنفيذ ملف SQL
                if process.returncode == 0:
                    logger.info("تم تحويل ملف DUMP إلى SQL بنجاح، جاري استيراد البيانات...")

                    # استيراد ملف SQL باستخدام psql
                    psql_cmd = [
                        'psql',
                        f"--dbname={database_config.database_name}",
                    ]

                    if database_config.username:
                        psql_cmd.append(f"--username={database_config.username}")

                    if database_config.host:
                        psql_cmd.append(f"--host={database_config.host}")

                    if database_config.port:
                        psql_cmd.append(f"--port={database_config.port}")

                    psql_cmd.append(f"--file={sql_file_path}")

                    with open(log_file_path, 'w') as log:
                        process = subprocess.run(
                            psql_cmd,
                            env=env,
                            stdout=log,
                            stderr=subprocess.STDOUT,
                            check=True
                        )

                    # حذف ملف SQL المؤقت
                    os.unlink(sql_file_path)
                else:
                    # قراءة سجل العملية
                    with open(log_file_path, 'r') as log:
                        log_content = log.read()

                    # رفع استثناء
                    raise Exception(f"فشل تحويل ملف DUMP إلى SQL: {log_content}")
            else:
                # استعادة النسخة الاحتياطية باستخدام pg_restore
                cmd = [
                    'pg_restore',
                    '--format=custom',
                    '--clean',
                    '--if-exists',
                    '--no-owner',  # تجاهل معلومات المالك
                    '--no-privileges',  # تجاهل معلومات الصلاحيات
                    f"--dbname={database_config.database_name}",
                ]

                if database_config.username:
                    cmd.append(f"--username={database_config.username}")

                if database_config.host:
                    cmd.append(f"--host={database_config.host}")

                if database_config.port:
                    cmd.append(f"--port={database_config.port}")

                cmd.append(file_path)

                # تنفيذ الأمر
                subprocess.run(cmd, check=True, env=env)
        finally:
            # حذف ملف السجل المؤقت
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def _restore_mysql_backup(self, database_config, file_path, clear_data):
        """استعادة نسخة احتياطية لقاعدة بيانات MySQL"""
        # حذف البيانات القديمة إذا لزم الأمر
        if clear_data:
            self._clear_mysql_database(database_config)

        # استعادة النسخة الاحتياطية
        cmd = [
            'mysql',
            f"--user={database_config.username}",
        ]

        if database_config.password:
            cmd.append(f"--password={database_config.password}")

        if database_config.host:
            cmd.append(f"--host={database_config.host}")

        if database_config.port:
            cmd.append(f"--port={database_config.port}")

        cmd.append(database_config.database_name)

        # تنفيذ الأمر
        with open(file_path, 'r') as f:
            subprocess.run(cmd, check=True, stdin=f)

    def _restore_sqlite_backup(self, database_config, file_path, clear_data):
        """استعادة نسخة احتياطية لقاعدة بيانات SQLite"""
        # نسخ ملف النسخة الاحتياطية إلى ملف قاعدة البيانات
        shutil.copy2(file_path, database_config.database_name)

    def _clear_postgresql_database(self, database_config):
        """حذف جميع البيانات من قاعدة بيانات PostgreSQL"""
        # إنشاء اتصال بقاعدة البيانات
        with connection.cursor() as cursor:
            # الحصول على قائمة الجداول
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = [row[0] for row in cursor.fetchall()]

            # حذف جميع البيانات من الجداول
            cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
            for table in tables:
                cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE;")

    def _clear_mysql_database(self, database_config):
        """حذف جميع البيانات من قاعدة بيانات MySQL"""
        # إنشاء اتصال بقاعدة البيانات
        with connection.cursor() as cursor:
            # تعطيل التحقق من المفاتيح الأجنبية
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

            # الحصول على قائمة الجداول
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]

            # حذف جميع البيانات من الجداول
            for table in tables:
                cursor.execute(f"TRUNCATE TABLE `{table}`;")

            # تفعيل التحقق من المفاتيح الأجنبية
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    def _import_json(self, file_path, database_config, clear_data):
        """استيراد ملف JSON"""
        # حذف البيانات القديمة إذا لزم الأمر
        if clear_data:
            call_command('flush', '--noinput')

        # استيراد البيانات
        call_command('loaddata', file_path)

    def _import_sql(self, file_path, database_config, clear_data):
        """استيراد ملف SQL"""
        if database_config.db_type == 'postgresql':
            self._restore_postgresql_backup(database_config, file_path, clear_data)
        elif database_config.db_type == 'mysql':
            self._restore_mysql_backup(database_config, file_path, clear_data)
        else:
            raise ValueError(f"نوع قاعدة البيانات '{database_config.db_type}' غير مدعوم لاستيراد ملفات SQL")

    def _import_dump(self, file_path, database_config, clear_data):
        """استيراد ملف DUMP"""
        if database_config.db_type == 'postgresql':
            self._restore_postgresql_backup(database_config, file_path, clear_data)
        else:
            raise ValueError(f"نوع قاعدة البيانات '{database_config.db_type}' غير مدعوم لاستيراد ملفات DUMP")

    def import_database_advanced(self, file_path, database_config=None, user=None, import_mode='merge',
                               clear_data=False, conflict_resolution='skip', import_settings=True,
                               import_users=False, import_customers=True, import_products=True,
                               import_orders=True, import_inspections=True):
        """
        استيراد قاعدة بيانات بخيارات متقدمة

        Args:
            file_path: مسار الملف
            database_config: إعدادات قاعدة البيانات
            user: المستخدم الذي أنشأ عملية الاستيراد
            import_mode: وضع الاستيراد (full, merge, update, selective)
            clear_data: هل يتم حذف البيانات القديمة
            conflict_resolution: طريقة معالجة التضارب (skip, overwrite, keep_both)
            import_settings: هل يتم استيراد الإعدادات
            import_users: هل يتم استيراد المستخدمين
            import_customers: هل يتم استيراد العملاء
            import_products: هل يتم استيراد المنتجات
            import_orders: هل يتم استيراد الطلبات
            import_inspections: هل يتم استيراد الفحوصات

        Returns:
            قاموس يحتوي على إحصائيات الاستيراد
        """
        if database_config is None:
            database_config = self.database

        # تحديد نوع الملف
        file_ext = os.path.splitext(file_path)[1].lower()

        # إحصائيات الاستيراد
        stats = {
            'total_records': 0,
            'imported_records': 0,
            'skipped_records': 0,
            'failed_records': 0,
        }

        # تحديد ما إذا كان يجب حذف البيانات القديمة
        should_clear_data = clear_data or import_mode == 'full'

        # استيراد البيانات حسب نوع الملف
        if file_ext == '.json':
            stats = self._import_json_advanced(
                file_path, database_config, should_clear_data, import_mode, conflict_resolution,
                import_settings, import_users, import_customers, import_products, import_orders, import_inspections
            )
        elif file_ext == '.sql':
            stats = self._import_sql_advanced(
                file_path, database_config, should_clear_data, import_mode, conflict_resolution,
                import_settings, import_users, import_customers, import_products, import_orders, import_inspections
            )
        elif file_ext == '.dump':
            stats = self._import_dump_advanced(
                file_path, database_config, should_clear_data, import_mode, conflict_resolution,
                import_settings, import_users, import_customers, import_products, import_orders, import_inspections
            )
        else:
            raise ValueError(f"نوع الملف '{file_ext}' غير مدعوم للاستيراد")

        return stats

    def _import_json_advanced(self, file_path, database_config, clear_data, import_mode, conflict_resolution,
                            import_settings, import_users, import_customers, import_products, import_orders, import_inspections):
        """استيراد ملف JSON بخيارات متقدمة"""
        # إحصائيات الاستيراد
        stats = {
            'total_records': 0,
            'imported_records': 0,
            'skipped_records': 0,
            'failed_records': 0,
        }

        # قراءة ملف JSON
        with open(file_path, 'r') as f:
            data = json.load(f)

        # حساب إجمالي السجلات
        stats['total_records'] = len(data)

        # تحديد الجداول التي سيتم استيرادها
        tables_to_import = []

        # إذا تم إلغاء تحديد جميع الخيارات، نقوم باستيراد جميع البيانات
        if not any([import_settings, import_users, import_customers, import_products, import_orders, import_inspections]):
            # استيراد جميع الجداول
            tables_to_import = None
            import_mode = 'full'
        elif import_mode == 'selective':
            # تحديد الجداول حسب الخيارات المحددة
            if import_settings:
                tables_to_import.extend(['auth_group', 'auth_permission', 'django_content_type', 'django_site', 'django_session'])

            if import_users:
                tables_to_import.extend(['auth_user', 'auth_user_groups', 'auth_user_user_permissions'])

            if import_customers:
                tables_to_import.extend(['customers_customer', 'customers_customeraddress', 'customers_customercontact'])

            if import_products:
                tables_to_import.extend(['inventory_product', 'inventory_category', 'inventory_supplier', 'inventory_stock'])

            if import_orders:
                tables_to_import.extend(['orders_order', 'orders_orderitem', 'orders_payment'])

            if import_inspections:
                tables_to_import.extend(['inspections_inspection', 'inspections_inspectionitem'])
        else:
            # استيراد جميع الجداول
            tables_to_import = None

        # حذف البيانات القديمة إذا لزم الأمر
        if clear_data:
            if tables_to_import:
                # حذف البيانات من الجداول المحددة فقط
                for table in tables_to_import:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
                    except Exception:
                        pass
            else:
                # حذف جميع البيانات
                call_command('flush', '--noinput')

        # استيراد البيانات
        try:
            # إنشاء ملف مؤقت للبيانات المحددة
            if tables_to_import:
                # تصفية البيانات حسب الجداول المحددة
                filtered_data = [item for item in data if item['model'].split('.')[0] in tables_to_import]

                # كتابة البيانات المصفاة إلى ملف مؤقت
                with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                    json.dump(filtered_data, temp_file)
                    temp_file_path = temp_file.name

                # استيراد البيانات من الملف المؤقت
                call_command('loaddata', temp_file_path)

                # حذف الملف المؤقت
                os.unlink(temp_file_path)

                # تحديث الإحصائيات
                stats['imported_records'] = len(filtered_data)
                stats['skipped_records'] = stats['total_records'] - stats['imported_records']
            else:
                # استيراد جميع البيانات
                call_command('loaddata', file_path)
                stats['imported_records'] = stats['total_records']
        except Exception as e:
            # تحديث الإحصائيات في حالة الخطأ
            stats['failed_records'] = stats['total_records'] - stats['imported_records'] - stats['skipped_records']
            raise

        return stats

    def _import_sql_advanced(self, file_path, database_config, clear_data, import_mode, conflict_resolution,
                           import_settings, import_users, import_customers, import_products, import_orders, import_inspections):
        """استيراد ملف SQL بخيارات متقدمة"""
        # إحصائيات الاستيراد
        stats = {
            'total_records': 0,
            'imported_records': 0,
            'skipped_records': 0,
            'failed_records': 0,
        }

        # تحديد الجداول التي سيتم استيرادها
        tables_to_import = []

        # إذا تم إلغاء تحديد جميع الخيارات، نقوم باستيراد جميع البيانات
        if not any([import_settings, import_users, import_customers, import_products, import_orders, import_inspections]):
            # استيراد جميع الجداول
            tables_to_import = []
            import_mode = 'full'
        elif import_mode == 'selective':
            # تحديد الجداول حسب الخيارات المحددة
            if import_settings:
                tables_to_import.extend(['auth_group', 'auth_permission', 'django_content_type', 'django_site', 'django_session'])

            if import_users:
                tables_to_import.extend(['auth_user', 'auth_user_groups', 'auth_user_user_permissions'])

            if import_customers:
                tables_to_import.extend(['customers_customer', 'customers_customeraddress', 'customers_customercontact'])

            if import_products:
                tables_to_import.extend(['inventory_product', 'inventory_category', 'inventory_supplier', 'inventory_stock'])

            if import_orders:
                tables_to_import.extend(['orders_order', 'orders_orderitem', 'orders_payment'])

            if import_inspections:
                tables_to_import.extend(['inspections_inspection', 'inspections_inspectionitem'])

        # استيراد البيانات حسب نوع قاعدة البيانات
        if database_config.db_type == 'postgresql':
            # استيراد البيانات من ملف SQL لقاعدة بيانات PostgreSQL
            if import_mode == 'selective' and tables_to_import:
                # إنشاء ملف مؤقت للأوامر SQL
                with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as temp_file:
                    # قراءة ملف SQL الأصلي
                    with open(file_path, 'r') as f:
                        sql_content = f.read()

                    # تصفية الأوامر SQL حسب الجداول المحددة
                    filtered_sql = ""
                    for table in tables_to_import:
                        # البحث عن أوامر SQL المتعلقة بالجدول
                        table_pattern = f"CREATE TABLE {table}"
                        if table_pattern in sql_content:
                            # استخراج أوامر SQL المتعلقة بالجدول
                            start_index = sql_content.find(table_pattern)
                            end_index = sql_content.find(";", start_index) + 1
                            filtered_sql += sql_content[start_index:end_index] + "\n"

                        # البحث عن أوامر INSERT المتعلقة بالجدول
                        insert_pattern = f"INSERT INTO {table}"
                        if insert_pattern in sql_content:
                            # استخراج أوامر INSERT المتعلقة بالجدول
                            lines = sql_content.split("\n")
                            for line in lines:
                                if insert_pattern in line:
                                    filtered_sql += line + "\n"

                    # كتابة الأوامر SQL المصفاة إلى الملف المؤقت
                    temp_file.write(filtered_sql.encode())
                    temp_file_path = temp_file.name

                # استيراد البيانات من الملف المؤقت
                self._restore_postgresql_backup(database_config, temp_file_path, clear_data)

                # حذف الملف المؤقت
                os.unlink(temp_file_path)
            else:
                # استيراد جميع البيانات
                self._restore_postgresql_backup(database_config, file_path, clear_data)
        elif database_config.db_type == 'mysql':
            # استيراد البيانات من ملف SQL لقاعدة بيانات MySQL
            if import_mode == 'selective' and tables_to_import:
                # إنشاء ملف مؤقت للأوامر SQL
                with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as temp_file:
                    # قراءة ملف SQL الأصلي
                    with open(file_path, 'r') as f:
                        sql_content = f.read()

                    # تصفية الأوامر SQL حسب الجداول المحددة
                    filtered_sql = ""
                    for table in tables_to_import:
                        # البحث عن أوامر SQL المتعلقة بالجدول
                        table_pattern = f"CREATE TABLE `{table}`"
                        if table_pattern in sql_content:
                            # استخراج أوامر SQL المتعلقة بالجدول
                            start_index = sql_content.find(table_pattern)
                            end_index = sql_content.find(";", start_index) + 1
                            filtered_sql += sql_content[start_index:end_index] + "\n"

                        # البحث عن أوامر INSERT المتعلقة بالجدول
                        insert_pattern = f"INSERT INTO `{table}`"
                        if insert_pattern in sql_content:
                            # استخراج أوامر INSERT المتعلقة بالجدول
                            lines = sql_content.split("\n")
                            for line in lines:
                                if insert_pattern in line:
                                    filtered_sql += line + "\n"

                    # كتابة الأوامر SQL المصفاة إلى الملف المؤقت
                    temp_file.write(filtered_sql.encode())
                    temp_file_path = temp_file.name

                # استيراد البيانات من الملف المؤقت
                self._restore_mysql_backup(database_config, temp_file_path, clear_data)

                # حذف الملف المؤقت
                os.unlink(temp_file_path)
            else:
                # استيراد جميع البيانات
                self._restore_mysql_backup(database_config, file_path, clear_data)
        else:
            raise ValueError(f"نوع قاعدة البيانات '{database_config.db_type}' غير مدعوم لاستيراد ملفات SQL")

        # تقدير عدد السجلات المستوردة
        stats['total_records'] = 1000  # تقدير تقريبي
        stats['imported_records'] = 1000  # تقدير تقريبي

        return stats

    def _import_dump_advanced(self, file_path, database_config, clear_data, import_mode, conflict_resolution,
                            import_settings, import_users, import_customers, import_products, import_orders, import_inspections):
        """استيراد ملف DUMP بخيارات متقدمة"""
        # إحصائيات الاستيراد
        stats = {
            'total_records': 0,
            'imported_records': 0,
            'skipped_records': 0,
            'failed_records': 0,
        }

        # استيراد البيانات حسب نوع قاعدة البيانات
        if database_config.db_type == 'postgresql':
            # تحديد الجداول التي سيتم استيرادها
            tables_to_import = []

            # إذا تم إلغاء تحديد جميع الخيارات، نقوم باستيراد جميع البيانات
            if not any([import_settings, import_users, import_customers, import_products, import_orders, import_inspections]):
                # استيراد جميع الجداول
                tables_to_import = []
                import_mode = 'full'
            elif import_mode == 'selective':
                # تحديد الجداول حسب الخيارات المحددة
                if import_settings:
                    tables_to_import.extend(['auth_group', 'auth_permission', 'django_content_type', 'django_site', 'django_session'])

                if import_users:
                    tables_to_import.extend(['auth_user', 'auth_user_groups', 'auth_user_user_permissions'])

                if import_customers:
                    tables_to_import.extend(['customers_customer', 'customers_customeraddress', 'customers_customercontact'])

                if import_products:
                    tables_to_import.extend(['inventory_product', 'inventory_category', 'inventory_supplier', 'inventory_stock'])

                if import_orders:
                    tables_to_import.extend(['orders_order', 'orders_orderitem', 'orders_payment'])

                if import_inspections:
                    tables_to_import.extend(['inspections_inspection', 'inspections_inspectionitem'])

                # استيراد الجداول المحددة فقط
                try:
                    # إنشاء ملف مؤقت للسجل
                    log_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log', mode='w+')
                    log_file_path = log_file.name
                    log_file.close()

                    # إعداد بيئة التنفيذ
                    env = os.environ.copy()
                    if database_config.password:
                        env['PGPASSWORD'] = database_config.password

                    # تحقق مما إذا كنا على Railway
                    is_railway = "railway" in (database_config.host or "")

                    # إذا كنا على Railway، نستخدم طريقة مختلفة للاستيراد
                    if is_railway:
                        logger.info("تم اكتشاف بيئة Railway، استخدام طريقة استيراد خاصة...")

                        # استخدام psql بدلاً من pg_restore على Railway
                        # أولاً، نقوم بتحويل ملف dump إلى SQL
                        sql_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sql')
                        sql_file_path = sql_file.name
                        sql_file.close()

                        # تحويل ملف dump إلى SQL
                        convert_cmd = [
                            'pg_restore',
                            '--format=custom',
                            '--file=' + sql_file_path,
                            file_path
                        ]

                        with open(log_file_path, 'w') as log:
                            process = subprocess.run(
                                convert_cmd,
                                env=env,
                                stdout=log,
                                stderr=subprocess.STDOUT,
                                check=False
                            )

                        # إذا نجح التحويل، نستخدم psql لتنفيذ ملف SQL
                        if process.returncode == 0:
                            logger.info("تم تحويل ملف DUMP إلى SQL بنجاح، جاري استيراد البيانات...")

                            # استيراد ملف SQL باستخدام psql
                            psql_cmd = [
                                'psql',
                                f"--dbname={database_config.database_name}",
                            ]

                            if database_config.username:
                                psql_cmd.append(f"--username={database_config.username}")

                            if database_config.host:
                                psql_cmd.append(f"--host={database_config.host}")

                            if database_config.port:
                                psql_cmd.append(f"--port={database_config.port}")

                            psql_cmd.append(f"--file={sql_file_path}")

                            with open(log_file_path, 'w') as log:
                                process = subprocess.run(
                                    psql_cmd,
                                    env=env,
                                    stdout=log,
                                    stderr=subprocess.STDOUT,
                                    check=False
                                )

                            # حذف ملف SQL المؤقت
                            os.unlink(sql_file_path)

                        # قراءة سجل العملية
                        with open(log_file_path, 'r') as log:
                            log_content = log.read()

                        # إذا فشلت العملية، نرفع استثناء
                        if process.returncode != 0:
                            raise Exception(f"فشل استيراد البيانات على Railway: {log_content}")
                    else:
                        # على البيئة المحلية، نستخدم pg_restore

                        # محاولة استيراد الملف بدون تحديد جداول (استيراد كامل)
                        cmd = [
                            'pg_restore',
                            '--format=custom',
                            '--clean',
                            '--if-exists',
                            '--no-owner',  # تجاهل معلومات المالك
                            '--no-privileges',  # تجاهل معلومات الصلاحيات
                            f"--dbname={database_config.database_name}",
                        ]

                        if database_config.username:
                            cmd.append(f"--username={database_config.username}")

                        if database_config.host:
                            cmd.append(f"--host={database_config.host}")

                        if database_config.port:
                            cmd.append(f"--port={database_config.port}")

                        cmd.append(file_path)

                        # تنفيذ الأمر مع توجيه المخرجات إلى ملف السجل
                        with open(log_file_path, 'w') as log:
                            process = subprocess.run(
                                cmd,
                                env=env,
                                stdout=log,
                                stderr=subprocess.STDOUT,
                                check=False  # لا نريد رفع استثناء في حالة الفشل
                            )

                        # قراءة سجل العملية
                        with open(log_file_path, 'r') as log:
                            log_content = log.read()

                        # إذا فشلت العملية، نحاول طريقة بديلة
                        if process.returncode != 0:
                            # تسجيل الخطأ
                            logger.warning(f"فشل استيراد الملف بالكامل: {log_content}")

                            # محاولة استيراد الجداول المحددة فقط
                            cmd = [
                                'pg_restore',
                                '--format=custom',
                                '--clean',
                                '--if-exists',
                                '--no-owner',
                                '--no-privileges',
                                '--data-only',  # استيراد البيانات فقط
                                f"--dbname={database_config.database_name}",
                            ]

                            if database_config.username:
                                cmd.append(f"--username={database_config.username}")

                            if database_config.host:
                                cmd.append(f"--host={database_config.host}")

                            if database_config.port:
                                cmd.append(f"--port={database_config.port}")

                            # إضافة الجداول المحددة
                            for table in tables_to_import:
                                cmd.append(f"--table={table}")

                            cmd.append(file_path)

                            # تنفيذ الأمر مع توجيه المخرجات إلى ملف السجل
                            with open(log_file_path, 'w') as log:
                                process = subprocess.run(
                                    cmd,
                                    env=env,
                                    stdout=log,
                                    stderr=subprocess.STDOUT,
                                    check=False
                                )

                            # قراءة سجل العملية
                            with open(log_file_path, 'r') as log:
                                log_content = log.read()

                            # إذا فشلت العملية مرة أخرى، نرفع استثناء
                            if process.returncode != 0:
                                raise Exception(f"فشل استيراد الجداول المحددة: {log_content}")

                    # حذف ملف السجل المؤقت
                    os.unlink(log_file_path)

                except Exception as e:
                    logger.error(f"حدث خطأ أثناء استيراد ملف DUMP: {str(e)}")
                    raise
            else:
                # استيراد جميع البيانات
                self._restore_postgresql_backup(database_config, file_path, clear_data)
        else:
            raise ValueError(f"نوع قاعدة البيانات '{database_config.db_type}' غير مدعوم لاستيراد ملفات DUMP")

        # تقدير عدد السجلات المستوردة
        stats['total_records'] = 1000  # تقدير تقريبي
        stats['imported_records'] = 1000  # تقدير تقريبي

        return stats
