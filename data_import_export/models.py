from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from accounts.models import User

class ImportExportLog(models.Model):
    """
    Model for logging import/export operations
    """
    OPERATION_TYPES = [
        ('import', _('استيراد')),
        ('export', _('تصدير')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('processing', _('قيد المعالجة')),
        ('completed', _('مكتمل')),
        ('failed', _('فشل')),
    ]
    
    operation_type = models.CharField(_('نوع العملية'), max_length=10, choices=OPERATION_TYPES)
    file_name = models.CharField(_('اسم الملف'), max_length=255)
    file = models.FileField(_('الملف'), upload_to='imports_exports/')
    
    # Target model information
    model_name = models.CharField(_('اسم النموذج'), max_length=100)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    is_multi_sheet = models.BooleanField(_('ملف متعدد الصفحات'), default=False)
    
    # Operation details
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='pending')
    records_count = models.PositiveIntegerField(_('عدد السجلات'), default=0)
    success_count = models.PositiveIntegerField(_('عدد النجاحات'), default=0)
    error_count = models.PositiveIntegerField(_('عدد الأخطاء'), default=0)
    
    # Error details
    error_details = models.TextField(_('تفاصيل الأخطاء'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    completed_at = models.DateTimeField(_('تاريخ الاكتمال'), null=True, blank=True)
    
    # User information
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='import_export_logs',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    
    class Meta:
        verbose_name = _('سجل استيراد/تصدير')
        verbose_name_plural = _('سجلات الاستيراد/التصدير')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.file_name} - {self.get_status_display()}"

class ImportTemplate(models.Model):
    """
    Model for import templates
    """
    name = models.CharField(_('اسم القالب'), max_length=100)
    description = models.TextField(_('الوصف'), blank=True)
    model_name = models.CharField(_('اسم النموذج'), max_length=100)
    file = models.FileField(_('ملف القالب'), upload_to='import_templates/')
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('قالب استيراد')
        verbose_name_plural = _('قوالب الاستيراد')
        ordering = ['name']
    
    def __str__(self):
        return self.name
