from django.db import models
from django.utils.translation import gettext_lazy as _

class SystemSettings(models.Model):
    """
    نموذج لإعدادات النظام العامة
    """
    CURRENCY_CHOICES = [
        ('SAR', _('ريال سعودي')),
        ('EGP', _('جنيه مصري')),
        ('USD', _('دولار أمريكي')),
        ('EUR', _('يورو')),
        ('AED', _('درهم إماراتي')),
        ('KWD', _('دينار كويتي')),
        ('QAR', _('ريال قطري')),
        ('BHD', _('دينار بحريني')),
        ('OMR', _('ريال عماني')),
    ]

    CURRENCY_SYMBOLS = {
        'SAR': 'ر.س',
        'EGP': 'ج.م',
        'USD': '$',
        'EUR': '€',
        'AED': 'د.إ',
        'KWD': 'د.ك',
        'QAR': 'ر.ق',
        'BHD': 'د.ب',
        'OMR': 'ر.ع',
    }

    name = models.CharField(_('اسم النظام'), max_length=100, default='نظام الخواجه')
    currency = models.CharField(_('العملة'), max_length=3, choices=CURRENCY_CHOICES, default='SAR')
    version = models.CharField(_('إصدار النظام'), max_length=20, default='1.0.0')
    enable_notifications = models.BooleanField(_('تفعيل الإشعارات'), default=True)
    enable_email_notifications = models.BooleanField(_('تفعيل إشعارات البريد الإلكتروني'), default=False)
    items_per_page = models.PositiveIntegerField(_('عدد العناصر في الصفحة'), default=20)
    low_stock_threshold = models.PositiveIntegerField(_('حد المخزون المنخفض (%)'), default=20)
    enable_analytics = models.BooleanField(_('تفعيل التحليلات'), default=True)
    maintenance_mode = models.BooleanField(_('وضع الصيانة'), default=False)
    maintenance_message = models.TextField(_('رسالة الصيانة'), blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('إعدادات النظام')
        verbose_name_plural = _('إعدادات النظام')

    def __str__(self):
        return self.name

    @property
    def currency_symbol(self):
        """الحصول على رمز العملة"""
        return self.CURRENCY_SYMBOLS.get(self.currency, self.currency)

    @classmethod
    def get_settings(cls):
        """الحصول على إعدادات النظام (إنشاء إذا لم تكن موجودة)"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
