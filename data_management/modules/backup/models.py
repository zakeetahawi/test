"""
نماذج وحدة النسخ الاحتياطي واستعادة البيانات
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import os

class BackupHistory(models.Model):
    """
    نموذج لتسجيل عمليات النسخ الاحتياطي
    """
    BACKUP_TYPE_CHOICES = [
        ('full', _('كامل')),
        ('partial', _('جزئي')),
        ('data_only', _('بيانات فقط')),
        ('schema_only', _('هيكل فقط')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('in_progress', _('قيد التنفيذ')),
        ('completed', _('مكتمل')),
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


class GoogleSheetsConfig(models.Model):
    """
    نموذج لإعدادات مزامنة Google Sheets
    """
    sheet_id = models.CharField(_('معرف جدول البيانات'), max_length=100)
    credentials_file = models.FileField(_('ملف بيانات الاعتماد'), upload_to='google_credentials/')
    is_active = models.BooleanField(_('نشط'), default=True)
    
    # إعدادات المزامنة
    sync_customers = models.BooleanField(_('مزامنة العملاء'), default=True)
    sync_products = models.BooleanField(_('مزامنة المنتجات'), default=True)
    sync_orders = models.BooleanField(_('مزامنة الطلبات'), default=True)
    sync_inventory = models.BooleanField(_('مزامنة المخزون'), default=True)
    sync_inspections = models.BooleanField(_('مزامنة المعاينات'), default=False)
    sync_installations = models.BooleanField(_('مزامنة التركيبات'), default=False)
    sync_company_info = models.BooleanField(_('مزامنة معلومات الشركة'), default=False)
    
    # جدولة المزامنة
    auto_sync = models.BooleanField(_('مزامنة تلقائية'), default=False)
    sync_interval = models.IntegerField(_('فترة المزامنة (بالدقائق)'), default=60)
    last_sync = models.DateTimeField(_('آخر مزامنة'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('إعدادات Google Sheets')
        verbose_name_plural = _('إعدادات Google Sheets')
    
    def __str__(self):
        return f"Google Sheets Config - {self.sheet_id}"


class SyncLog(models.Model):
    """
    نموذج لتسجيل عمليات المزامنة
    """
    STATUS_CHOICES = [
        ('success', _('نجاح')),
        ('partial', _('نجاح جزئي')),
        ('failed', _('فشل')),
    ]
    
    timestamp = models.DateTimeField(_('وقت المزامنة'), auto_now_add=True)
    config = models.ForeignKey(GoogleSheetsConfig, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES)
    records_synced = models.IntegerField(_('عدد السجلات المزامنة'), default=0)
    errors = models.TextField(_('الأخطاء'), blank=True)
    
    class Meta:
        verbose_name = _('سجل المزامنة')
        verbose_name_plural = _('سجلات المزامنة')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Sync Log - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.get_status_display()}"
