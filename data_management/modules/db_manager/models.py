"""
نماذج وحدة إدارة قواعد البيانات
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid

class DatabaseConfig(models.Model):
    """
    نموذج لإعدادات قاعدة البيانات
    """
    DB_TYPES = [
        ('postgresql', _('PostgreSQL')),
        ('mysql', _('MySQL')),
        ('sqlite', _('SQLite')),
    ]

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

    class Meta:
        verbose_name = _('إعداد قاعدة البيانات')
        verbose_name_plural = _('إعدادات قواعد البيانات')
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_db_type_display()})"

    def save(self, *args, **kwargs):
        # إذا كانت هذه قاعدة البيانات الافتراضية، تأكد من أن جميع قواعد البيانات الأخرى ليست افتراضية
        if self.is_default:
            DatabaseConfig.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)

        super().save(*args, **kwargs)


class DatabaseBackup(models.Model):
    """
    نموذج لنسخ قاعدة البيانات الاحتياطية
    """
    BACKUP_TYPES = [
        ('full', _('كامل')),
        ('schema', _('هيكل فقط')),
        ('data', _('بيانات فقط')),
    ]

    name = models.CharField(_('اسم النسخة الاحتياطية'), max_length=255)
    description = models.TextField(_('وصف'), blank=True, null=True)
    file = models.FileField(_('ملف النسخة الاحتياطية'), upload_to='db_backups/')
    backup_type = models.CharField(_('نوع النسخة الاحتياطية'), max_length=20, choices=BACKUP_TYPES, default='full')
    database_config = models.ForeignKey(DatabaseConfig, on_delete=models.CASCADE, related_name='backups', verbose_name=_('إعداد قاعدة البيانات'))
    size = models.BigIntegerField(_('الحجم (بايت)'), default=0)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='data_management_created_backups', verbose_name=_('تم الإنشاء بواسطة'))

    class Meta:
        verbose_name = _('نسخة احتياطية لقاعدة البيانات')
        verbose_name_plural = _('النسخ الاحتياطية لقواعد البيانات')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def get_size_display(self):
        """عرض حجم الملف بشكل مقروء"""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class DatabaseImport(models.Model):
    """
    نموذج لاستيراد قاعدة البيانات
    """
    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('processing', _('قيد المعالجة')),
        ('completed', _('مكتمل')),
        ('failed', _('فشل')),
    ]

    file = models.FileField(_('ملف الاستيراد'), upload_to='db_imports/')
    database_config = models.ForeignKey(DatabaseConfig, on_delete=models.CASCADE, related_name='imports', verbose_name=_('إعداد قاعدة البيانات'))
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='pending')
    log = models.TextField(_('سجل العملية'), blank=True, null=True)
    clear_data = models.BooleanField(_('حذف البيانات القديمة'), default=False)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    completed_at = models.DateTimeField(_('تاريخ الاكتمال'), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='data_management_created_imports', verbose_name=_('تم الإنشاء بواسطة'))

    class Meta:
        verbose_name = _('استيراد قاعدة البيانات')
        verbose_name_plural = _('عمليات استيراد قواعد البيانات')
        ordering = ['-created_at']

    def __str__(self):
        return f"Import {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')} - {self.get_status_display()}"


class SetupToken(models.Model):
    """
    نموذج لرموز الإعداد
    """
    token = models.UUIDField(_('الرمز'), default=uuid.uuid4, editable=False, unique=True)
    is_used = models.BooleanField(_('مستخدم'), default=False)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    expires_at = models.DateTimeField(_('تاريخ انتهاء الصلاحية'))

    class Meta:
        verbose_name = _('رمز الإعداد')
        verbose_name_plural = _('رموز الإعداد')
        ordering = ['-created_at']

    def __str__(self):
        return f"Setup Token - {self.token} - {'Used' if self.is_used else 'Unused'}"

    @property
    def is_valid(self):
        """التحقق من صلاحية الرمز"""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()
