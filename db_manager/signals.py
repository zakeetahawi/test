from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.db.models.signals import request_started

from .models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken

import os
import logging
import random
from datetime import timedelta

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


@receiver(request_started)
def cleanup_sessions_on_request(sender, **kwargs):
    """تنظيف الجلسات القديمة والمكررة بشكل دوري"""
    # تنفيذ التنظيف بشكل عشوائي (بنسبة 1%)
    # لتجنب تنفيذ العملية مع كل طلب
    if random.random() < 0.01:  # 1% من الطلبات
        try:
            # البحث عن الجلسات المكررة
            session_keys = Session.objects.values_list('session_key', flat=True)
            duplicate_keys = set()
            unique_keys = set()

            for key in session_keys:
                if key in unique_keys:
                    duplicate_keys.add(key)
                else:
                    unique_keys.add(key)

            # حذف الجلسات المكررة
            for key in duplicate_keys:
                # الاحتفاظ بأحدث جلسة وحذف البقية
                sessions = Session.objects.filter(session_key=key).order_by('-expire_date')
                if sessions.count() > 1:
                    # الاحتفاظ بأول جلسة (الأحدث) وحذف البقية
                    for session in sessions[1:]:
                        session.delete()

            # حذف الجلسات المنتهية الصلاحية
            cutoff_date = timezone.now() - timedelta(days=1)
            Session.objects.filter(expire_date__lt=cutoff_date).delete()

            logger.info("تم تنظيف الجلسات القديمة والمكررة")
        except Exception as e:
            logger.error(f"خطأ أثناء تنظيف الجلسات: {e}")
