from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone

from .models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken

import os
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=DatabaseConfig)
def handle_database_config_pre_save(sender, instance, **kwargs):
    """معالجة إشارة ما قبل حفظ إعداد قاعدة البيانات"""
    # إذا كان هذا الإعداد هو الافتراضي، قم بإلغاء تعيين الإعدادات الأخرى كافتراضية
    if instance.is_default:
        DatabaseConfig.objects.exclude(pk=instance.pk).update(is_default=False)


@receiver(post_save, sender=DatabaseBackup)
def handle_database_backup_post_save(sender, instance, created, **kwargs):
    """معالجة إشارة ما بعد حفظ النسخة الاحتياطية"""
    if created:
        # تسجيل إنشاء نسخة احتياطية جديدة
        logger.info(f"تم إنشاء نسخة احتياطية جديدة: {instance.name}")


@receiver(pre_delete, sender=DatabaseBackup)
def handle_database_backup_pre_delete(sender, instance, **kwargs):
    """معالجة إشارة ما قبل حذف النسخة الاحتياطية"""
    # حذف ملف النسخة الاحتياطية
    if instance.file:
        try:
            # حذف الملف من نظام الملفات
            if os.path.exists(instance.file.path):
                os.remove(instance.file.path)
        except Exception as e:
            logger.error(f"خطأ أثناء حذف ملف النسخة الاحتياطية: {e}")


@receiver(post_save, sender=DatabaseImport)
def handle_database_import_post_save(sender, instance, created, **kwargs):
    """معالجة إشارة ما بعد حفظ عملية الاستيراد"""
    if created:
        # تسجيل بدء عملية استيراد جديدة
        logger.info(f"تم بدء عملية استيراد جديدة: {instance.id}")
    else:
        # تسجيل تحديث حالة عملية الاستيراد
        if instance.status == 'completed':
            logger.info(f"تم اكتمال عملية الاستيراد: {instance.id}")
        elif instance.status == 'failed':
            logger.error(f"فشلت عملية الاستيراد: {instance.id}, السبب: {instance.log}")


@receiver(pre_delete, sender=DatabaseImport)
def handle_database_import_pre_delete(sender, instance, **kwargs):
    """معالجة إشارة ما قبل حذف عملية الاستيراد"""
    # حذف ملف الاستيراد
    if instance.file:
        try:
            # حذف الملف من نظام الملفات
            if os.path.exists(instance.file.path):
                os.remove(instance.file.path)
        except Exception as e:
            logger.error(f"خطأ أثناء حذف ملف الاستيراد: {e}")


@receiver(post_save, sender=SetupToken)
def handle_setup_token_post_save(sender, instance, created, **kwargs):
    """معالجة إشارة ما بعد حفظ رمز الإعداد"""
    if created:
        # تسجيل إنشاء رمز إعداد جديد
        logger.info(f"تم إنشاء رمز إعداد جديد: {instance.token}")
    else:
        # تسجيل تحديث حالة رمز الإعداد
        if instance.is_used and instance.used_at:
            logger.info(f"تم استخدام رمز الإعداد: {instance.token} في {instance.used_at}")
