from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import os
import uuid
from datetime import datetime

class DatabaseConfig(models.Model):
    """نموذج لتخزين إعدادات قواعد البيانات"""

    DB_TYPES = (
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('sqlite', 'SQLite'),
    )

    name = models.CharField(_('اسم قاعدة البيانات'), max_length=100)
    db_type = models.CharField(_('نوع قاعدة البيانات'), max_length=20, choices=DB_TYPES)
    host = models.CharField(_('المضيف'), max_length=255, blank=True, null=True)
    port = models.CharField(_('المنفذ'), max_length=10, blank=True, null=True)
    username = models.CharField(_('اسم المستخدم'), max_length=100, blank=True, null=True)
    password = models.CharField(_('كلمة المرور'), max_length=100, blank=True, null=True)
    database_name = models.CharField(_('اسم قاعدة البيانات'), max_length=100, blank=True, null=True)
    connection_string = models.TextField(_('سلسلة الاتصال'), blank=True, null=True)
    is_active = models.BooleanField(_('نشط'), default=False)
    is_default = models.BooleanField(_('افتراضي'), default=False)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('إعداد قاعدة البيانات')
        verbose_name_plural = _('إعدادات قواعد البيانات')
        ordering = ['-is_default', '-is_active', 'name']


class DatabaseBackup(models.Model):
    """نموذج لتخزين معلومات النسخ الاحتياطية لقواعد البيانات"""

    BACKUP_TYPES = (
        ('full', _('نسخة كاملة')),
        ('partial', _('نسخة جزئية')),
    )

    name = models.CharField(_('اسم النسخة الاحتياطية'), max_length=255)
    description = models.TextField(_('وصف'), blank=True, null=True)
    file = models.FileField(_('ملف النسخة الاحتياطية'), upload_to='db_backups/')
    backup_type = models.CharField(_('نوع النسخة الاحتياطية'), max_length=20, choices=BACKUP_TYPES, default='full')
    database_config = models.ForeignKey(DatabaseConfig, on_delete=models.CASCADE, related_name='backups', verbose_name=_('إعداد قاعدة البيانات'))
    size = models.BigIntegerField(_('الحجم (بايت)'), default=0)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_backups', verbose_name=_('تم الإنشاء بواسطة'))

    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        # حساب حجم الملف عند الحفظ
        if self.file and os.path.exists(self.file.path):
            self.size = os.path.getsize(self.file.path)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('نسخة احتياطية لقاعدة البيانات')
        verbose_name_plural = _('النسخ الاحتياطية لقواعد البيانات')
        ordering = ['-created_at']


class DatabaseImport(models.Model):
    """نموذج لتخزين معلومات عمليات استيراد قواعد البيانات"""

    STATUS_CHOICES = (
        ('pending', _('قيد الانتظار')),
        ('in_progress', _('قيد التنفيذ')),
        ('completed', _('مكتمل')),
        ('failed', _('فشل')),
    )

    file = models.FileField(_('ملف الاستيراد'), upload_to='db_imports/')
    database_config = models.ForeignKey(DatabaseConfig, on_delete=models.CASCADE, related_name='imports', verbose_name=_('إعداد قاعدة البيانات'))
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='pending')
    log = models.TextField(_('سجل العملية'), blank=True, null=True)
    clear_data = models.BooleanField(_('حذف البيانات القديمة'), default=False)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    completed_at = models.DateTimeField(_('تاريخ الاكتمال'), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_imports', verbose_name=_('تم الإنشاء بواسطة'))

    def __str__(self):
        return f"استيراد {self.id} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = _('استيراد قاعدة بيانات')
        verbose_name_plural = _('عمليات استيراد قواعد البيانات')
        ordering = ['-created_at']


class SetupToken(models.Model):
    """نموذج لتخزين رموز الإعداد الأولي للنظام"""

    token = models.UUIDField(_('رمز الإعداد'), default=uuid.uuid4, editable=False, unique=True)
    is_used = models.BooleanField(_('تم استخدامه'), default=False)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    expires_at = models.DateTimeField(_('تاريخ انتهاء الصلاحية'))
    used_at = models.DateTimeField(_('تاريخ الاستخدام'), null=True, blank=True)

    def __str__(self):
        return f"رمز إعداد {self.token}"

    @property
    def is_expired(self):
        return datetime.now().astimezone() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired

    class Meta:
        verbose_name = _('رمز إعداد')
        verbose_name_plural = _('رموز الإعداد')
        ordering = ['-created_at']
