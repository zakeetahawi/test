"""
خدمة النسخ الاحتياطي المجدولة
"""

import os
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

from odoo_db_manager.models import Database, Backup, BackupSchedule
from odoo_db_manager.services.backup_service import BackupService

logger = logging.getLogger(__name__)

class ScheduledBackupService:
    """خدمة النسخ الاحتياطي المجدولة"""

    def __init__(self):
        """تهيئة الخدمة"""
        self.scheduler = None
        self.backup_service = BackupService()

    def start(self):
        """بدء تشغيل المجدول"""
        if self.scheduler and self.scheduler.running:
            logger.info("المجدول يعمل بالفعل")
            return

        logger.info("بدء تشغيل مجدول النسخ الاحتياطي")
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # إضافة المهام المجدولة
        self._schedule_all_backups()
        
        # بدء تشغيل المجدول
        self.scheduler.start()
        logger.info("تم بدء تشغيل مجدول النسخ الاحتياطي")

    def stop(self):
        """إيقاف تشغيل المجدول"""
        if self.scheduler and self.scheduler.running:
            logger.info("إيقاف تشغيل مجدول النسخ الاحتياطي")
            self.scheduler.shutdown()
            self.scheduler = None
            logger.info("تم إيقاف تشغيل مجدول النسخ الاحتياطي")

    def _schedule_all_backups(self):
        """جدولة جميع النسخ الاحتياطية النشطة"""
        # حذف جميع المهام السابقة
        if self.scheduler:
            self.scheduler.remove_all_jobs()
        
        # الحصول على جميع جدولات النسخ الاحتياطية النشطة
        schedules = BackupSchedule.objects.filter(is_active=True)
        logger.info(f"جدولة {schedules.count()} نسخة احتياطية")
        
        for schedule in schedules:
            self._schedule_backup(schedule)

    def _schedule_backup(self, schedule):
        """جدولة نسخة احتياطية واحدة"""
        if not self.scheduler:
            logger.error("المجدول غير متاح")
            return
        
        # حساب موعد التشغيل القادم إذا لم يكن محدداً
        if not schedule.next_run:
            schedule.calculate_next_run()
        
        # إنشاء معرف المهمة
        job_id = f"backup_{schedule.id}"
        
        # تحديد معاملات التكرار
        trigger_args = {}
        
        if schedule.frequency == 'hourly':
            trigger = 'interval'
            trigger_args['hours'] = 1
        elif schedule.frequency == 'daily':
            trigger = 'cron'
            trigger_args['hour'] = schedule.hour
            trigger_args['minute'] = schedule.minute
        elif schedule.frequency == 'weekly':
            trigger = 'cron'
            trigger_args['day_of_week'] = schedule.day_of_week
            trigger_args['hour'] = schedule.hour
            trigger_args['minute'] = schedule.minute
        elif schedule.frequency == 'monthly':
            trigger = 'cron'
            trigger_args['day'] = schedule.day_of_month
            trigger_args['hour'] = schedule.hour
            trigger_args['minute'] = schedule.minute
        else:
            logger.error(f"تكرار غير معروف: {schedule.frequency}")
            return
        
        # إضافة المهمة إلى المجدول
        self.scheduler.add_job(
            self._create_backup,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs={
                'schedule_id': schedule.id
            },
            **trigger_args
        )
        
        logger.info(f"تمت جدولة النسخة الاحتياطية {schedule.name} (ID: {schedule.id}) بتكرار {schedule.get_frequency_display()}")

    def _create_backup(self, schedule_id):
        """إنشاء نسخة احتياطية مجدولة"""
        try:
            # الحصول على جدولة النسخة الاحتياطية
            schedule = BackupSchedule.objects.get(id=schedule_id)
            
            # التحقق من أن الجدولة نشطة
            if not schedule.is_active:
                logger.info(f"تم تخطي النسخة الاحتياطية {schedule.name} (ID: {schedule.id}) لأنها غير نشطة")
                return
            
            logger.info(f"بدء إنشاء النسخة الاحتياطية المجدولة {schedule.name} (ID: {schedule.id})")
            
            # إنشاء النسخة الاحتياطية
            backup = self.backup_service.create_backup(
                database_id=schedule.database.id,
                name=f"{schedule.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                user=schedule.created_by,
                backup_type=schedule.backup_type
            )
            
            # تحديث وقت آخر تشغيل
            schedule.last_run = timezone.now()
            
            # حساب موعد التشغيل القادم
            schedule.calculate_next_run()
            
            # حذف النسخ الاحتياطية القديمة إذا تجاوزت الحد الأقصى
            self._cleanup_old_backups(schedule)
            
            logger.info(f"تم إنشاء النسخة الاحتياطية المجدولة {schedule.name} (ID: {schedule.id}) بنجاح")
            
            return backup
        except Exception as e:
            logger.error(f"حدث خطأ أثناء إنشاء النسخة الاحتياطية المجدولة: {str(e)}")
            return None

    def _cleanup_old_backups(self, schedule):
        """حذف النسخ الاحتياطية القديمة إذا تجاوزت الحد الأقصى"""
        try:
            # الحصول على النسخ الاحتياطية المرتبطة بهذه الجدولة
            backups = Backup.objects.filter(
                database=schedule.database,
                backup_type=schedule.backup_type,
                is_scheduled=True
            ).order_by('-created_at')
            
            # التحقق من عدد النسخ الاحتياطية
            if backups.count() > schedule.max_backups:
                # حساب عدد النسخ الاحتياطية التي يجب حذفها
                to_delete_count = backups.count() - schedule.max_backups
                
                # الحصول على النسخ الاحتياطية التي سيتم حذفها
                to_delete = backups[schedule.max_backups:]
                
                logger.info(f"حذف {to_delete.count()} نسخة احتياطية قديمة لجدولة {schedule.name} (ID: {schedule.id})")
                
                # حذف النسخ الاحتياطية
                for backup in to_delete:
                    # حذف ملف النسخة الاحتياطية
                    if os.path.exists(backup.file_path):
                        os.unlink(backup.file_path)
                    
                    # حذف سجل النسخة الاحتياطية
                    backup.delete()
                
                logger.info(f"تم حذف {to_delete.count()} نسخة احتياطية قديمة بنجاح")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء حذف النسخ الاحتياطية القديمة: {str(e)}")

# إنشاء نسخة واحدة من الخدمة
scheduled_backup_service = ScheduledBackupService()
