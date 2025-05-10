import logging
from django_apscheduler.models import DjangoJobExecution
from django.conf import settings
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from django_apscheduler import util
from django.core.management import call_command
import os
import hashlib
import gzip
import tempfile
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model

from .services.auto_sync_service import auto_sync_data
from .models import GoogleSheetsConfig, AutoBackupConfig, BackupHistory, BackupNotificationSetting
from .services.backup_service import BackupService

logger = logging.getLogger(__name__)


@util.close_old_connections
def perform_sync():
    """
    وظيفة تنفذ المزامنة التلقائية مع Google Sheets
    """
    logger.info("بدء المزامنة التلقائية في %s", datetime.now())
    try:
        success, count = auto_sync_data(force=False)
        if success:
            logger.info("اكتمال المزامنة التلقائية بنجاح. تمت مزامنة %s سجل.", count)
        else:
            logger.warning("لم تتم المزامنة، ربما بسبب انتهاء الفاصل الزمني.")
    except Exception as e:
        logger.error("حدث خطأ أثناء المزامنة التلقائية: %s", str(e))


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):  # 7 days
    """
    مهمة لحذف سجلات التنفيذ القديمة للمهام المجدولة
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def calculate_next_backup(interval, time):
    """حساب موعد النسخ الاحتياطي التالي"""
    now = timezone.now()
    today = now.date()
    backup_time = datetime.combine(today, time)
    backup_datetime = timezone.make_aware(backup_time)
    
    if backup_datetime <= now:
        if interval == 'daily':
            backup_datetime += timedelta(days=1)
        elif interval == 'weekly':
            backup_datetime += timedelta(weeks=1)
        elif interval == 'monthly':
            # حساب اليوم المقابل في الشهر التالي
            if backup_datetime.month == 12:
                next_date = backup_datetime.replace(year=backup_datetime.year + 1, month=1)
            else:
                next_date = backup_datetime.replace(month=backup_datetime.month + 1)
            backup_datetime = next_date
    
    return backup_datetime


def compress_file(input_path):
    """ضغط ملف النسخة الاحتياطية"""
    output_path = input_path + '.gz'
    with open(input_path, 'rb') as f_in:
        with gzip.open(output_path, 'wb') as f_out:
            f_out.writelines(f_in)
    return output_path


def encrypt_file(input_path, key):
    """تشفير ملف النسخة الاحتياطية"""
    fernet = Fernet(key)
    output_path = input_path + '.enc'
    with open(input_path, 'rb') as f:
        file_data = f.read()
    encrypted_data = fernet.encrypt(file_data)
    with open(output_path, 'wb') as f:
        f.write(encrypted_data)
    return output_path


def cleanup_old_backups(retention_days):
    """حذف النسخ الاحتياطية القديمة"""
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    old_backups = BackupHistory.objects.filter(
        timestamp__lt=cutoff_date,
        backup_type='auto'
    )
    
    for backup in old_backups:
        try:
            if backup.backup_location and os.path.exists(backup.backup_location):
                os.remove(backup.backup_location)
            backup.delete()
        except Exception as e:
            print(f"Error cleaning up backup {backup.id}: {str(e)}")


def perform_auto_backup():
    """تنفيذ النسخ الاحتياطي التلقائي"""
    try:
        config = AutoBackupConfig.objects.first()
        if not config or not config.enabled:
            return
        
        now = timezone.now()
        if config.next_backup and now < config.next_backup:
            return
        
        # إنشاء ملف مؤقت للنسخ الاحتياطي
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        filename = f'auto_backup_{timestamp}.psql'
        temp_path = os.path.join(settings.DBBACKUP_TMP_DIR, filename)
        
        # إنشاء النسخة الاحتياطية
        call_command('dbbackup', '--output-filename', temp_path)
        
        # معالجة الملف (ضغط وتشفير)
        final_path = temp_path
        if config.compression_enabled:
            compressed_path = compress_file(final_path)
            os.remove(final_path)
            final_path = compressed_path
        
        if config.encryption_enabled and config.encryption_key:
            encrypted_path = encrypt_file(final_path, config.encryption_key.encode())
            os.remove(final_path)
            final_path = encrypted_path
        
        # تسجيل النسخة الاحتياطية
        with open(final_path, 'rb') as f:
            file_content = f.read()
            file_size = len(file_content)
            checksum = hashlib.sha256(file_content).hexdigest()
        
        backup = BackupHistory.objects.create(
            backup_type='auto',
            file_name=os.path.basename(final_path),
            file_size=file_size,
            status='success',
            file_checksum=checksum,
            backup_location=final_path,
            is_compressed=config.compression_enabled,
            is_encrypted=config.encryption_enabled,
            metadata={
                'created_at': now.isoformat(),
                'backup_config': {
                    'interval': config.interval,
                    'compression': config.compression_enabled,
                    'encryption': config.encryption_enabled
                }
            }
        )
        
        # تحديث وقت النسخ الاحتياطي التالي
        config.last_backup = now
        config.next_backup = calculate_next_backup(config.interval, config.time)
        config.save()
        
        # تنظيف النسخ القديمة
        cleanup_old_backups(config.retention_days)
        
    except Exception as e:
        print(f"Error during auto backup: {str(e)}")
        if 'final_path' in locals() and os.path.exists(final_path):
            os.remove(final_path)


def auto_backup_job():
    """المهمة المجدولة للنسخ الاحتياطي التلقائي"""
    config = AutoBackupConfig.objects.first()
    
    # التحقق من تفعيل النسخ الاحتياطي التلقائي
    if not config or not config.enabled:
        logger.info("النسخ الاحتياطي التلقائي غير مفعل.")
        return
    
    # التحقق من موعد النسخ الاحتياطي
    now = timezone.now()
    current_time = now.time()
    
    # الوقت اليومي المحدد للنسخ الاحتياطي
    scheduled_time = config.time
    
    # التحقق من آخر نسخ احتياطي
    if config.last_backup:
        if config.interval == 'daily':
            # التحقق إذا كان النسخ اليومي قد تم بالفعل اليوم
            if config.last_backup.date() == now.date() and current_time.hour >= scheduled_time.hour:
                return
        
        elif config.interval == 'weekly':
            # التحقق إذا كان النسخ الأسبوعي قد تم بالفعل هذا الأسبوع
            last_week_date = now - timedelta(days=7)
            if config.last_backup >= last_week_date:
                return
        
        elif config.interval == 'monthly':
            # التحقق إذا كان النسخ الشهري قد تم بالفعل هذا الشهر
            if config.last_backup.month == now.month and config.last_backup.year == now.year:
                return
    
    # الحصول على مستخدم النظام (Admin)
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    # إنشاء النسخة الاحتياطية
    try:
        logger.info("بدء مهمة النسخ الاحتياطي التلقائي...")
        backup_service = BackupService(user=admin_user)
        result = backup_service.create_backup(backup_type='auto')
        
        if result['success']:
            # تحديث آخر وقت للنسخ الاحتياطي
            config.last_backup = now
            
            # حساب الموعد التالي للنسخ الاحتياطي
            if config.interval == 'daily':
                config.next_backup = timezone.make_aware(
                    datetime.combine(now.date() + timedelta(days=1), scheduled_time)
                )
            elif config.interval == 'weekly':
                config.next_backup = timezone.make_aware(
                    datetime.combine(now.date() + timedelta(days=7), scheduled_time)
                )
            elif config.interval == 'monthly':
                # حساب تاريخ الشهر التالي (أخذ اليوم الحالي)
                next_month = now.month + 1
                next_year = now.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                
                try:
                    next_date = datetime(next_year, next_month, now.day)
                except ValueError:  # في حالة كان اليوم غير موجود في الشهر التالي (مثل 31 فبراير)
                    # استخدام آخر يوم في الشهر التالي
                    if next_month == 2:
                        next_date = datetime(next_year, next_month, 28)
                    else:
                        next_date = datetime(next_year, next_month, 30)
                
                config.next_backup = timezone.make_aware(
                    datetime.combine(next_date, scheduled_time)
                )
            
            config.save()
            
            # إرسال إشعارات النجاح
            BackupNotificationSetting.notify_admins(
                subject="نسخة احتياطية تلقائية ناجحة",
                message=f"تم إنشاء نسخة احتياطية تلقائية بنجاح. حجم الملف: {result['file_size'] / (1024*1024):.2f} MB",
                backup=BackupHistory.objects.get(id=result['backup_id']),
                is_error=False
            )
            
            # تنظيف النسخ القديمة
            backup_service.clean_old_backups()
            
            logger.info("تم إنشاء النسخة الاحتياطية التلقائية بنجاح.")
        else:
            # إرسال إشعارات الفشل
            BackupNotificationSetting.notify_admins(
                subject="فشل النسخة الاحتياطية التلقائية",
                message=f"فشل إنشاء النسخة الاحتياطية التلقائية: {result.get('error', 'خطأ غير معروف')}",
                is_error=True
            )
            
            logger.error(f"فشل إنشاء النسخة الاحتياطية التلقائية: {result.get('error')}")
    
    except Exception as e:
        logger.exception(f"حدث خطأ أثناء تنفيذ مهمة النسخ الاحتياطي التلقائي: {str(e)}")
        
        # إرسال إشعارات الخطأ
        BackupNotificationSetting.notify_admins(
            subject="خطأ في النسخ الاحتياطي التلقائي",
            message=f"حدث خطأ أثناء تنفيذ مهمة النسخ الاحتياطي التلقائي: {str(e)}",
            is_error=True
        )


def start_scheduler():
    """
    بدء جدولة المهام للمزامنة التلقائية
    """
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # الحصول على إعدادات المزامنة من قاعدة البيانات
    config = GoogleSheetsConfig.objects.filter(is_active=True).first()
    sync_interval = 1  # القيمة الافتراضية دقيقة واحدة
    
    # استخدام القيمة من قاعدة البيانات إذا كانت موجودة
    if config and config.sync_interval_minutes:
        sync_interval = max(1, config.sync_interval_minutes)  # لا تقل عن دقيقة واحدة

    # إضافة وظيفة المزامنة التلقائية
    scheduler.add_job(
        perform_sync,
        'interval',
        minutes=sync_interval,
        id='sync_with_google_sheets',
        replace_existing=True
    )

    # إضافة وظيفة حذف سجلات التنفيذ القديمة للمهام المجدولة
    scheduler.add_job(
        delete_old_job_executions,
        trigger='cron',
        day_of_week='mon',
        hour='00',
        minute='00',
        id='delete_old_job_executions',
        replace_existing=True
    )

    # إضافة وظيفة النسخ الاحتياطي التلقائي
    scheduler.add_job(
        auto_backup_job,
        trigger='cron',
        hour='02',
        minute='00',
        id='auto_backup',
        replace_existing=True
    )

    try:
        logger.info("بدء تشغيل جدولة المهام مع فترة مزامنة %s دقيقة...", sync_interval)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("تم إيقاف جدولة المهام")
        scheduler.shutdown()