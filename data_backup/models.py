from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone
import json

class GoogleSheetsConfig(models.Model):
    """تكوين المزامنة مع جداول Google"""
    spreadsheet_id = models.CharField(max_length=255, verbose_name=_('معرف جدول البيانات'))
    credentials_file = models.FileField(upload_to='google_credentials/', verbose_name=_('ملف بيانات الاعتماد'))
    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))
    
    # الإعدادات للمزامنة التلقائية
    auto_sync_enabled = models.BooleanField(default=False, verbose_name=_('تفعيل المزامنة التلقائية'))
    sync_interval_minutes = models.PositiveIntegerField(default=60, verbose_name=_('فترة المزامنة (بالدقائق)'))
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name=_('آخر مزامنة'))
    
    # الجداول التي سيتم مزامنتها
    sync_customers = models.BooleanField(default=True, verbose_name=_('مزامنة العملاء'))
    sync_orders = models.BooleanField(default=True, verbose_name=_('مزامنة الطلبات'))
    sync_products = models.BooleanField(default=True, verbose_name=_('مزامنة المنتجات'))
    sync_inspections = models.BooleanField(default=True, verbose_name=_('مزامنة المعاينات'))
    sync_installations = models.BooleanField(default=True, verbose_name=_('مزامنة التركيبات'))
    
    # إضافة خيارات مزامنة جديدة للمعلومات النصية
    sync_company_info = models.BooleanField(default=True, verbose_name=_('مزامنة معلومات الشركة'))
    sync_contact_details = models.BooleanField(default=True, verbose_name=_('مزامنة بيانات التواصل'))
    sync_system_settings = models.BooleanField(default=True, verbose_name=_('مزامنة إعدادات النظام'))
    
    def __str__(self):
        return f"إعدادات مزامنة جوجل {self.id}"
    
    class Meta:
        verbose_name = _('إعدادات مزامنة جوجل')
        verbose_name_plural = _('إعدادات مزامنة جوجل')

class SyncLog(models.Model):
    """سجل عمليات المزامنة"""
    STATUS_CHOICES = [
        ('success', _('ناجحة')),
        ('partial', _('نجاح جزئي')),
        ('failed', _('فاشلة')),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('التاريخ والوقت'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name=_('الحالة'))
    details = models.TextField(blank=True, null=True, verbose_name=_('التفاصيل'))
    records_synced = models.PositiveIntegerField(default=0, verbose_name=_('عدد السجلات المزامنة'))
    triggered_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('تمت بواسطة'))
    
    def __str__(self):
        return f"مزامنة {self.get_status_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = _('سجل المزامنة')
        verbose_name_plural = _('سجلات المزامنة')
        ordering = ['-timestamp']

class SystemConfiguration(models.Model):
    """إعدادات النظام والبيانات النصية القابلة للمزامنة"""
    CATEGORY_CHOICES = [
        ('company_info', _('معلومات الشركة')),
        ('contact_details', _('بيانات التواصل')),
        ('system_settings', _('إعدادات النظام')),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name=_('القسم'))
    key = models.CharField(max_length=100, verbose_name=_('المفتاح'))
    value = models.TextField(blank=True, null=True, verbose_name=_('القيمة'))
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('الوصف'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))
    
    class Meta:
        verbose_name = _('إعداد النظام')
        verbose_name_plural = _('إعدادات النظام')
        unique_together = ('category', 'key')  # لا يمكن تكرار نفس المفتاح في نفس القسم
        ordering = ['category', 'key']
    
    def __str__(self):
        return f"{self.get_category_display()}: {self.key}"

class BackupHistory(models.Model):
    """نموذج لتتبع وتسجيل عمليات النسخ الاحتياطي"""
    
    BACKUP_TYPE_CHOICES = [
        ('auto', _('تلقائي')),
        ('manual', _('يدوي')),
        ('pre_import', _('قبل الاستيراد')),
    ]

    STATUS_CHOICES = [
        ('success', _('نجاح')),
        ('failed', _('فشل')),
        ('restored', _('تمت الاستعادة')),
    ]

    timestamp = models.DateTimeField(_('وقت النسخ'), auto_now_add=True)
    backup_type = models.CharField(_('نوع النسخ'), max_length=20, choices=BACKUP_TYPE_CHOICES)
    file_name = models.CharField(_('اسم الملف'), max_length=255)
    file_size = models.IntegerField(_('حجم الملف'))
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(_('رسالة الخطأ'), blank=True, null=True)
    metadata = models.JSONField(_('البيانات الوصفية'), default=dict)
    file_checksum = models.CharField(_('التحقق من سلامة الملف'), max_length=64)
    backup_location = models.CharField(_('موقع النسخة الاحتياطية'), max_length=255)
    is_compressed = models.BooleanField(_('مضغوط'), default=True)
    is_encrypted = models.BooleanField(_('مشفر'), default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('تم الإنشاء بواسطة')
    )

    class Meta:
        verbose_name = _('سجل النسخ الاحتياطي')
        verbose_name_plural = _('سجلات النسخ الاحتياطي')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['backup_type', 'status']),
        ]

    def __str__(self):
        return f"{self.get_backup_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    def get_file_size_display(self):
        """عرض حجم الملف بشكل مقروء"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def validate_backup_file(self):
        """التحقق من سلامة ملف النسخ الاحتياطي"""
        import hashlib
        import os
        
        if not os.path.exists(self.backup_location):
            return False
            
        sha256_hash = hashlib.sha256()
        with open(self.backup_location, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest() == self.file_checksum

class AutoBackupConfig(models.Model):
    """إعدادات النسخ الاحتياطي التلقائي"""
    INTERVAL_CHOICES = [
        ('daily', _('يومياً')),
        ('weekly', _('أسبوعياً')),
        ('monthly', _('شهرياً')),
    ]

    enabled = models.BooleanField(_('تفعيل النسخ الاحتياطي التلقائي'), default=False)
    interval = models.CharField(_('الفترة'), max_length=20, choices=INTERVAL_CHOICES, default='daily')
    time = models.TimeField(_('وقت التنفيذ'), help_text=_('وقت تنفيذ النسخ الاحتياطي (بالتوقيت المحلي)'))
    retention_days = models.PositiveIntegerField(
        _('مدة الاحتفاظ (بالأيام)'),
        default=30,
        validators=[MinValueValidator(1)],
        help_text=_('عدد الأيام التي سيتم الاحتفاظ بالنسخ الاحتياطية خلالها')
    )
    compression_enabled = models.BooleanField(_('تفعيل الضغط'), default=True)
    encryption_enabled = models.BooleanField(_('تفعيل التشفير'), default=False)
    encryption_key = models.CharField(
        _('مفتاح التشفير'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('مفتاح التشفير للنسخ الاحتياطية (اتركه فارغاً إذا لم يكن التشفير مفعلاً)')
    )
    last_backup = models.DateTimeField(_('آخر نسخ احتياطي'), null=True, blank=True)
    next_backup = models.DateTimeField(_('النسخ الاحتياطي التالي'), null=True, blank=True)

    class Meta:
        verbose_name = _('إعدادات النسخ الاحتياطي التلقائي')
        verbose_name_plural = _('إعدادات النسخ الاحتياطي التلقائي')

    def __str__(self):
        return f"إعدادات النسخ الاحتياطي التلقائي - {self.get_interval_display()}"

class BackupNotificationSetting(models.Model):
    """إعدادات إشعارات النسخ الاحتياطي"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('المستخدم'))
    notify_on_success = models.BooleanField(_('إشعار عند نجاح النسخ'), default=True)
    notify_on_failure = models.BooleanField(_('إشعار عند فشل النسخ'), default=True)
    notify_on_restore = models.BooleanField(_('إشعار عند الاستعادة'), default=True)
    email_notifications = models.BooleanField(_('إشعارات البريد الإلكتروني'), default=True)

    class Meta:
        verbose_name = _('إعدادات الإشعارات')
        verbose_name_plural = _('إعدادات الإشعارات')

    def __str__(self):
        return f"إعدادات إشعارات {self.user.get_full_name() or self.user.username}"

    @classmethod
    def notify_admins(cls, subject, message, backup=None, is_error=False):
        """إرسال إشعار للمشرفين"""
        admins = get_user_model().objects.filter(is_superuser=True)
        for admin in admins:
            settings = cls.objects.get_or_create(user=admin)[0]
            
            if (is_error and settings.notify_on_failure) or \
               (not is_error and settings.notify_on_success) or \
               (backup and backup.status == 'restored' and settings.notify_on_restore):
                
                if settings.email_notifications and admin.email:
                    context = {
                        'user': admin,
                        'message': message,
                        'backup': backup,
                        'is_error': is_error
                    }
                    email_body = render_to_string('data_backup/email/notification.html', context)
                    
                    send_mail(
                        subject=subject,
                        message=message,
                        html_message=email_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin.email],
                        fail_silently=True
                    )

class CloudStorageConfig(models.Model):
    STORAGE_TYPES = (
        ('google_drive', 'Google Drive'),
        ('s3', 'Amazon S3'),
    )

    storage_type = models.CharField(max_length=20, choices=STORAGE_TYPES)
    is_active = models.BooleanField(default=False)
    auto_upload = models.BooleanField(default=False)
    retention_period = models.IntegerField(default=30)  # بالأيام

    # إعدادات Google Drive
    google_credentials = models.FileField(upload_to='google_credentials/', null=True, blank=True)
    google_folder_id = models.CharField(max_length=100, null=True, blank=True)

    # إعدادات Amazon S3
    aws_access_key = models.CharField(max_length=100, null=True, blank=True)
    aws_secret_key = models.CharField(max_length=100, null=True, blank=True)
    aws_bucket_name = models.CharField(max_length=100, null=True, blank=True)
    aws_region = models.CharField(max_length=50, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'إعدادات التخزين السحابي'
        verbose_name_plural = 'إعدادات التخزين السحابي'

class BackupMetrics(models.Model):
    backup_date = models.DateTimeField(default=timezone.now)
    backup_size = models.BigIntegerField()  # بالبايت
    successful = models.BooleanField(default=True)
    duration = models.FloatField()  # بالثواني
    storage_type = models.CharField(max_length=20, choices=CloudStorageConfig.STORAGE_TYPES)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'إحصائيات النسخ الاحتياطي'
        verbose_name_plural = 'إحصائيات النسخ الاحتياطي'
        ordering = ['-backup_date']

    @classmethod
    def get_success_rate(cls, days=30):
        """حساب معدل نجاح النسخ الاحتياطي"""
        start_date = timezone.now() - timezone.timedelta(days=days)
        total = cls.objects.filter(backup_date__gte=start_date).count()
        if total == 0:
            return 0
        successful = cls.objects.filter(
            backup_date__gte=start_date,
            successful=True
        ).count()
        return (successful / total) * 100

    @classmethod
    def get_average_duration(cls, days=7):
        """حساب متوسط وقت النسخ الاحتياطي"""
        start_date = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(
            backup_date__gte=start_date,
            successful=True
        ).aggregate(avg_duration=models.Avg('duration'))['avg_duration'] or 0
