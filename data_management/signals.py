"""
إشارات تطبيق إدارة البيانات
"""

import os
import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings

from .modules.import_export.models import ImportExportLog
from .modules.backup.models import BackupHistory, GoogleSheetsConfig, SyncLog
from .modules.db_manager.models import DatabaseConfig, DatabaseBackup, DatabaseImport

logger = logging.getLogger(__name__)

# إشارات وحدة استيراد وتصدير البيانات

@receiver(post_save, sender=ImportExportLog)
def handle_import_export_log_save(sender, instance, created, **kwargs):
    """معالجة حفظ سجل الاستيراد/التصدير"""
    if created:
        logger.info(f"تم إنشاء سجل استيراد/تصدير جديد: {instance}")
    else:
        logger.info(f"تم تحديث سجل استيراد/تصدير: {instance}")

@receiver(post_delete, sender=ImportExportLog)
def handle_import_export_log_delete(sender, instance, **kwargs):
    """معالجة حذف سجل الاستيراد/التصدير"""
    # حذف الملف المرتبط بالسجل
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
    
    logger.info(f"تم حذف سجل استيراد/تصدير: {instance}")

# إشارات وحدة النسخ الاحتياطي

@receiver(post_save, sender=BackupHistory)
def handle_backup_history_save(sender, instance, created, **kwargs):
    """معالجة حفظ سجل النسخ الاحتياطي"""
    if created:
        logger.info(f"تم إنشاء سجل نسخ احتياطي جديد: {instance}")
    else:
        logger.info(f"تم تحديث سجل نسخ احتياطي: {instance}")

@receiver(post_delete, sender=BackupHistory)
def handle_backup_history_delete(sender, instance, **kwargs):
    """معالجة حذف سجل النسخ الاحتياطي"""
    # حذف ملف النسخة الاحتياطية
    if instance.backup_location and os.path.isfile(instance.backup_location):
        try:
            os.remove(instance.backup_location)
            logger.info(f"تم حذف ملف النسخة الاحتياطية: {instance.backup_location}")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء حذف ملف النسخة الاحتياطية: {str(e)}")
    
    logger.info(f"تم حذف سجل نسخ احتياطي: {instance}")

@receiver(post_save, sender=GoogleSheetsConfig)
def handle_google_sheets_config_save(sender, instance, created, **kwargs):
    """معالجة حفظ إعدادات Google Sheets"""
    if created:
        logger.info(f"تم إنشاء إعدادات Google Sheets جديدة: {instance}")
    else:
        logger.info(f"تم تحديث إعدادات Google Sheets: {instance}")
    
    # إذا كانت هذه الإعدادات نشطة، تأكد من أن جميع الإعدادات الأخرى غير نشطة
    if instance.is_active:
        GoogleSheetsConfig.objects.filter(is_active=True).exclude(pk=instance.pk).update(is_active=False)

# إشارات وحدة إدارة قواعد البيانات

@receiver(pre_save, sender=DatabaseConfig)
def handle_database_config_pre_save(sender, instance, **kwargs):
    """معالجة ما قبل حفظ إعدادات قاعدة البيانات"""
    # إذا كانت هذه قاعدة البيانات الافتراضية، تأكد من أن جميع قواعد البيانات الأخرى ليست افتراضية
    if instance.is_default:
        DatabaseConfig.objects.filter(is_default=True).exclude(pk=instance.pk).update(is_default=False)
    
    # إذا كانت هذه قاعدة البيانات نشطة، تأكد من أن جميع قواعد البيانات الأخرى غير نشطة
    if instance.is_active:
        DatabaseConfig.objects.filter(is_active=True).exclude(pk=instance.pk).update(is_active=False)

@receiver(post_save, sender=DatabaseConfig)
def handle_database_config_save(sender, instance, created, **kwargs):
    """معالجة حفظ إعدادات قاعدة البيانات"""
    if created:
        logger.info(f"تم إنشاء إعدادات قاعدة بيانات جديدة: {instance}")
    else:
        logger.info(f"تم تحديث إعدادات قاعدة بيانات: {instance}")

@receiver(post_save, sender=DatabaseBackup)
def handle_database_backup_save(sender, instance, created, **kwargs):
    """معالجة حفظ نسخة احتياطية لقاعدة البيانات"""
    if created:
        logger.info(f"تم إنشاء نسخة احتياطية جديدة لقاعدة البيانات: {instance}")
    else:
        logger.info(f"تم تحديث نسخة احتياطية لقاعدة البيانات: {instance}")

@receiver(post_delete, sender=DatabaseBackup)
def handle_database_backup_delete(sender, instance, **kwargs):
    """معالجة حذف نسخة احتياطية لقاعدة البيانات"""
    # حذف ملف النسخة الاحتياطية
    if instance.file:
        if os.path.isfile(instance.file.path):
            try:
                os.remove(instance.file.path)
                logger.info(f"تم حذف ملف النسخة الاحتياطية: {instance.file.path}")
            except Exception as e:
                logger.error(f"حدث خطأ أثناء حذف ملف النسخة الاحتياطية: {str(e)}")
    
    logger.info(f"تم حذف نسخة احتياطية لقاعدة البيانات: {instance}")

@receiver(post_save, sender=DatabaseImport)
def handle_database_import_save(sender, instance, created, **kwargs):
    """معالجة حفظ استيراد قاعدة البيانات"""
    if created:
        logger.info(f"تم إنشاء استيراد جديد لقاعدة البيانات: {instance}")
    else:
        # إذا تم تحديث الحالة إلى 'completed'، قم بتحديث وقت الاكتمال
        if instance.status == 'completed' and not instance.completed_at:
            instance.completed_at = timezone.now()
            instance.save(update_fields=['completed_at'])
        
        logger.info(f"تم تحديث استيراد قاعدة البيانات: {instance}")

@receiver(post_delete, sender=DatabaseImport)
def handle_database_import_delete(sender, instance, **kwargs):
    """معالجة حذف استيراد قاعدة البيانات"""
    # حذف ملف الاستيراد
    if instance.file:
        if os.path.isfile(instance.file.path):
            try:
                os.remove(instance.file.path)
                logger.info(f"تم حذف ملف الاستيراد: {instance.file.path}")
            except Exception as e:
                logger.error(f"حدث خطأ أثناء حذف ملف الاستيراد: {str(e)}")
    
    logger.info(f"تم حذف استيراد قاعدة البيانات: {instance}")
