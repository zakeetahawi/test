"""
خدمات وحدة إدارة قواعد البيانات
"""

import os
import subprocess
import tempfile
import json
import datetime
import uuid
from django.conf import settings
from django.utils import timezone
from django.db import connection, connections
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.crypto import get_random_string

from .models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken

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
        return reverse('data_management:db_setup_with_token', args=[token.token])
    
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
        
        # استعادة النسخة الاحتياطية
        cmd = [
            'pg_restore',
            '--format=custom',
            '--clean',
            '--if-exists',
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
        env = os.environ.copy()
        if database_config.password:
            env['PGPASSWORD'] = database_config.password
        
        subprocess.run(cmd, check=True, env=env)
    
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
