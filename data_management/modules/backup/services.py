"""
خدمات وحدة النسخ الاحتياطي
"""

import os
import subprocess
import tempfile
import hashlib
import shutil
import gzip
import json
import datetime
from django.conf import settings
from django.utils import timezone
from django.db import connection, models
from django.core.management import call_command
from django.contrib.auth import get_user_model

from .models import BackupHistory, GoogleSheetsConfig, SyncLog

class BackupService:
    """خدمة النسخ الاحتياطي"""

    def __init__(self):
        """تهيئة الخدمة"""
        self.backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, backup_type='full', is_compressed=True, is_encrypted=False, created_by=None):
        """
        إنشاء نسخة احتياطية

        Args:
            backup_type: نوع النسخة الاحتياطية (full, partial, data_only, schema_only)
            is_compressed: هل يتم ضغط النسخة الاحتياطية
            is_encrypted: هل يتم تشفير النسخة الاحتياطية
            created_by: المستخدم الذي أنشأ النسخة الاحتياطية

        Returns:
            كائن BackupHistory
        """
        # إنشاء اسم الملف
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"backup_{backup_type}_{timestamp}"

        # تحديد نوع الملف
        if is_compressed:
            file_name += '.sql.gz'
        else:
            file_name += '.sql'

        # مسار الملف
        file_path = os.path.join(self.backup_dir, file_name)

        # إنشاء النسخة الاحتياطية
        if backup_type == 'full':
            self._create_full_backup(file_path, is_compressed)
        elif backup_type == 'data_only':
            self._create_data_only_backup(file_path, is_compressed)
        elif backup_type == 'schema_only':
            self._create_schema_only_backup(file_path, is_compressed)
        else:
            raise ValueError(f"نوع النسخة الاحتياطية '{backup_type}' غير مدعوم")

        # حساب حجم الملف
        file_size = os.path.getsize(file_path)

        # حساب التحقق من سلامة الملف
        file_checksum = self._calculate_checksum(file_path)

        # إنشاء سجل النسخة الاحتياطية
        backup = BackupHistory.objects.create(
            timestamp=timezone.now(),
            backup_type=backup_type,
            file_name=file_name,
            file_size=file_size,
            status='completed',
            file_checksum=file_checksum,
            backup_location=file_path,
            is_compressed=is_compressed,
            is_encrypted=is_encrypted,
            created_by=created_by,
            metadata={
                'database_name': settings.DATABASES['default']['NAME'],
                'database_engine': settings.DATABASES['default']['ENGINE'],
                'django_version': settings.DJANGO_VERSION,
                'backup_date': timezone.now().isoformat(),
            }
        )

        return backup

    def restore_backup(self, backup_id):
        """
        استعادة نسخة احتياطية

        Args:
            backup_id: معرف النسخة الاحتياطية

        Returns:
            True إذا تمت الاستعادة بنجاح
        """
        # الحصول على النسخة الاحتياطية
        backup = BackupHistory.objects.get(id=backup_id)

        # التحقق من وجود الملف
        if not os.path.exists(backup.backup_location):
            raise FileNotFoundError(f"ملف النسخة الاحتياطية '{backup.backup_location}' غير موجود")

        # استعادة النسخة الاحتياطية
        if backup.is_compressed:
            self._restore_compressed_backup(backup.backup_location)
        else:
            self._restore_backup(backup.backup_location)

        # تحديث حالة النسخة الاحتياطية
        backup.status = 'restored'
        backup.save()

        return True

    def get_backup_statistics(self):
        """
        الحصول على إحصائيات النسخ الاحتياطي

        Returns:
            قاموس يحتوي على إحصائيات النسخ الاحتياطي
        """
        total_backups = BackupHistory.objects.count()
        successful_backups = BackupHistory.objects.filter(status='completed').count()
        failed_backups = BackupHistory.objects.filter(status='failed').count()
        restored_backups = BackupHistory.objects.filter(status='restored').count()

        # حساب إجمالي حجم النسخ الاحتياطية
        total_size = BackupHistory.objects.filter(status='completed').aggregate(total_size=models.Sum('file_size'))['total_size'] or 0

        # الحصول على آخر نسخة احتياطية
        last_backup = BackupHistory.objects.filter(status='completed').order_by('-timestamp').first()

        return {
            'total_backups': total_backups,
            'successful_backups': successful_backups,
            'failed_backups': failed_backups,
            'restored_backups': restored_backups,
            'total_size': total_size,
            'last_backup': last_backup,
        }

    def _create_full_backup(self, file_path, is_compressed=True):
        """إنشاء نسخة احتياطية كاملة"""
        if is_compressed:
            with gzip.open(file_path, 'wb') as f:
                call_command('dumpdata', '--all', '--indent=2', stdout=f)
        else:
            with open(file_path, 'w') as f:
                call_command('dumpdata', '--all', '--indent=2', stdout=f)

    def _create_data_only_backup(self, file_path, is_compressed=True):
        """إنشاء نسخة احتياطية للبيانات فقط"""
        if is_compressed:
            with gzip.open(file_path, 'wb') as f:
                call_command('dumpdata', '--all', '--indent=2', exclude=['contenttypes', 'auth.permission'], stdout=f)
        else:
            with open(file_path, 'w') as f:
                call_command('dumpdata', '--all', '--indent=2', exclude=['contenttypes', 'auth.permission'], stdout=f)

    def _create_schema_only_backup(self, file_path, is_compressed=True):
        """إنشاء نسخة احتياطية للهيكل فقط"""
        # استخدام pg_dump لإنشاء نسخة احتياطية للهيكل فقط
        db_settings = settings.DATABASES['default']
        cmd = [
            'pg_dump',
            '--schema-only',
            '--no-owner',
            '--no-privileges',
            f"--dbname={db_settings['NAME']}",
        ]

        if 'USER' in db_settings:
            cmd.append(f"--username={db_settings['USER']}")

        if 'HOST' in db_settings:
            cmd.append(f"--host={db_settings['HOST']}")

        if 'PORT' in db_settings:
            cmd.append(f"--port={db_settings['PORT']}")

        if is_compressed:
            cmd.append(f"--file={file_path}.temp")
            subprocess.run(cmd, check=True)

            # ضغط الملف
            with open(f"{file_path}.temp", 'rb') as f_in:
                with gzip.open(file_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # حذف الملف المؤقت
            os.remove(f"{file_path}.temp")
        else:
            cmd.append(f"--file={file_path}")
            subprocess.run(cmd, check=True)

    def _restore_backup(self, file_path):
        """استعادة نسخة احتياطية"""
        call_command('flush', '--noinput')
        call_command('loaddata', file_path)

    def _restore_compressed_backup(self, file_path):
        """استعادة نسخة احتياطية مضغوطة"""
        # إنشاء ملف مؤقت
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name

        # فك ضغط الملف
        with gzip.open(file_path, 'rb') as f_in:
            with open(temp_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # استعادة النسخة الاحتياطية
        call_command('flush', '--noinput')
        call_command('loaddata', temp_path)

        # حذف الملف المؤقت
        os.remove(temp_path)

    def _calculate_checksum(self, file_path):
        """حساب التحقق من سلامة الملف"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


class GoogleSheetsService:
    """خدمة مزامنة Google Sheets"""

    def __init__(self, config_id=None):
        """
        تهيئة الخدمة

        Args:
            config_id: معرف إعدادات Google Sheets
        """
        if config_id:
            self.config = GoogleSheetsConfig.objects.get(id=config_id)
        else:
            self.config = GoogleSheetsConfig.objects.filter(is_active=True).first()

        if not self.config:
            raise ValueError("لم يتم العثور على إعدادات Google Sheets نشطة")

    def sync_data(self):
        """
        مزامنة البيانات مع Google Sheets

        Returns:
            كائن SyncLog
        """
        # إنشاء سجل المزامنة
        sync_log = SyncLog.objects.create(
            config=self.config,
            status='success',
            records_synced=0
        )

        try:
            # مزامنة البيانات
            records_synced = 0
            errors = []

            # مزامنة العملاء
            if self.config.sync_customers:
                try:
                    customer_count = self._sync_customers()
                    records_synced += customer_count
                except Exception as e:
                    errors.append(f"خطأ في مزامنة العملاء: {str(e)}")

            # مزامنة المنتجات
            if self.config.sync_products:
                try:
                    product_count = self._sync_products()
                    records_synced += product_count
                except Exception as e:
                    errors.append(f"خطأ في مزامنة المنتجات: {str(e)}")

            # مزامنة الطلبات
            if self.config.sync_orders:
                try:
                    order_count = self._sync_orders()
                    records_synced += order_count
                except Exception as e:
                    errors.append(f"خطأ في مزامنة الطلبات: {str(e)}")

            # تحديث سجل المزامنة
            sync_log.records_synced = records_synced

            if errors:
                sync_log.status = 'partial' if records_synced > 0 else 'failed'
                sync_log.errors = '\n'.join(errors)

            # تحديث وقت آخر مزامنة
            self.config.last_sync = timezone.now()
            self.config.save()

            sync_log.save()

            return sync_log
        except Exception as e:
            # تحديث سجل المزامنة في حالة الخطأ
            sync_log.status = 'failed'
            sync_log.errors = str(e)
            sync_log.save()

            raise

    def _sync_customers(self):
        """مزامنة العملاء"""
        # تنفيذ المزامنة
        # ...

        return 0

    def _sync_products(self):
        """مزامنة المنتجات"""
        # تنفيذ المزامنة
        # ...

        return 0

    def _sync_orders(self):
        """مزامنة الطلبات"""
        # تنفيذ المزامنة
        # ...

        return 0
