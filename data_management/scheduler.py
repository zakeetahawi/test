"""
مجدول المهام لتطبيق إدارة البيانات
"""

import logging
from django.conf import settings
from django.utils import timezone
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import sys

from .modules.backup.models import GoogleSheetsConfig
from .modules.backup.services import BackupService, GoogleSheetsService
from .modules.db_manager.models import DatabaseConfig

logger = logging.getLogger(__name__)

def start_scheduler():
    """بدء تشغيل المجدول"""
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # جدولة النسخ الاحتياطي التلقائي
    scheduler.add_job(
        create_automatic_backup,
        trigger=CronTrigger(hour="3", minute="0"),  # تشغيل في الساعة 3 صباحاً كل يوم
        id="create_automatic_backup",
        max_instances=1,
        replace_existing=True,
    )
    logger.info("تمت جدولة مهمة النسخ الاحتياطي التلقائي.")
    
    # جدولة مزامنة Google Sheets
    scheduler.add_job(
        sync_google_sheets,
        trigger=CronTrigger(minute="*/30"),  # تشغيل كل 30 دقيقة
        id="sync_google_sheets",
        max_instances=1,
        replace_existing=True,
    )
    logger.info("تمت جدولة مهمة مزامنة Google Sheets.")
    
    # جدولة تنظيف النسخ الاحتياطية القديمة
    scheduler.add_job(
        cleanup_old_backups,
        trigger=CronTrigger(day_of_week="sun", hour="4", minute="0"),  # تشغيل في الساعة 4 صباحاً كل يوم أحد
        id="cleanup_old_backups",
        max_instances=1,
        replace_existing=True,
    )
    logger.info("تمت جدولة مهمة تنظيف النسخ الاحتياطية القديمة.")
    
    # جدولة تنظيف وظائف المجدول القديمة
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(day_of_week="mon", hour="00", minute="00"),  # تشغيل في الساعة 12 منتصف الليل كل يوم اثنين
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )
    logger.info("تمت جدولة مهمة تنظيف وظائف المجدول القديمة.")
    
    try:
        logger.info("بدء تشغيل المجدول...")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("إيقاف المجدول...")
        scheduler.shutdown()
        logger.info("تم إيقاف المجدول بنجاح!")


def create_automatic_backup():
    """إنشاء نسخة احتياطية تلقائية"""
    try:
        logger.info("بدء إنشاء نسخة احتياطية تلقائية...")
        
        # إنشاء خدمة النسخ الاحتياطي
        backup_service = BackupService()
        
        # إنشاء نسخة احتياطية
        backup = backup_service.create_backup(
            backup_type='full',
            is_compressed=True,
            is_encrypted=False
        )
        
        logger.info(f"تم إنشاء نسخة احتياطية تلقائية بنجاح: {backup.file_name}")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء إنشاء النسخة الاحتياطية التلقائية: {str(e)}")


def sync_google_sheets():
    """مزامنة Google Sheets"""
    try:
        # التحقق من وجود إعدادات نشطة
        config = GoogleSheetsConfig.objects.filter(is_active=True, auto_sync=True).first()
        
        if not config:
            logger.info("لا توجد إعدادات نشطة لمزامنة Google Sheets.")
            return
        
        # التحقق من وقت آخر مزامنة
        if config.last_sync:
            time_since_last_sync = timezone.now() - config.last_sync
            if time_since_last_sync.total_seconds() < config.sync_interval * 60:
                logger.info("لم يحن وقت المزامنة بعد.")
                return
        
        logger.info("بدء مزامنة Google Sheets...")
        
        # إنشاء خدمة المزامنة
        sync_service = GoogleSheetsService(config.id)
        
        # مزامنة البيانات
        sync_log = sync_service.sync_data()
        
        logger.info(f"تمت مزامنة Google Sheets بنجاح: {sync_log.records_synced} سجل.")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء مزامنة Google Sheets: {str(e)}")


def cleanup_old_backups():
    """تنظيف النسخ الاحتياطية القديمة"""
    try:
        from .modules.backup.models import BackupHistory
        import datetime
        
        logger.info("بدء تنظيف النسخ الاحتياطية القديمة...")
        
        # حذف النسخ الاحتياطية الأقدم من 30 يوم
        thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
        old_backups = BackupHistory.objects.filter(timestamp__lt=thirty_days_ago)
        
        # حفظ أحدث 5 نسخ احتياطية على الأقل
        latest_backups = BackupHistory.objects.order_by('-timestamp')[:5]
        latest_ids = [backup.id for backup in latest_backups]
        
        # حذف النسخ الاحتياطية القديمة مع استثناء أحدث 5 نسخ
        old_backups = old_backups.exclude(id__in=latest_ids)
        
        count = old_backups.count()
        old_backups.delete()
        
        logger.info(f"تم حذف {count} نسخة احتياطية قديمة.")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تنظيف النسخ الاحتياطية القديمة: {str(e)}")


def delete_old_job_executions(max_age=604_800):
    """
    حذف تنفيذات الوظائف القديمة من قاعدة البيانات
    
    يتم الاحتفاظ بسجلات تنفيذ الوظائف لمدة 7 أيام افتراضياً
    """
    try:
        from django_apscheduler.models import DjangoJobExecution
        
        logger.info("حذف تنفيذات الوظائف القديمة من قاعدة البيانات...")
        
        # حذف تنفيذات الوظائف القديمة
        DjangoJobExecution.objects.delete_old_job_executions(max_age)
        
        logger.info("تم حذف تنفيذات الوظائف القديمة بنجاح.")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء حذف تنفيذات الوظائف القديمة: {str(e)}")
