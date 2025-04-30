from django.db import models
from django.utils.translation import gettext_lazy as _

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
