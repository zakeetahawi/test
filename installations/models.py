from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from accounts.models import User, Branch
from orders.models import Order
from customers.models import Customer

class Installation(models.Model):
    """
    Model for installation requests
    """
    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('scheduled', _('تم الجدولة')),
        ('in_progress', _('قيد التنفيذ')),
        ('completed', _('مكتمل')),
        ('cancelled', _('ملغي')),
    ]
    team_leader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lead_installations',
        verbose_name=_('قائد الفريق')
    )

    
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='installations',
        verbose_name=_('الطلب')
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='installations',
        verbose_name=_('العميل')
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='installations',
        verbose_name=_('الفرع')
    )
    invoice_number = models.CharField(
        _('رقم الفاتورة'),
        max_length=50
    )
    scheduled_date = models.DateTimeField(
        _('موعد التركيب'),
        null=True,
        blank=True
    )
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_verified = models.BooleanField(
        _('تم التحقق من السداد'),
        default=False
    )
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_installations',
        verbose_name=_('الفني المسؤول')
    )
    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_installations',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    created_at = models.DateTimeField(
        _('تاريخ الإنشاء'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('تاريخ التحديث'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('تركيب')
        verbose_name_plural = _('التركيبات')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{_('تركيب')} #{self.id} - {self.customer.name}"
    
    def clean(self):
        # Verify payment before scheduling
        if self.status == 'scheduled' and not self.payment_verified:
            raise ValidationError(_('يجب التحقق من السداد قبل جدولة التركيب'))
        
        # Only allow users to create installations in their branch
        if self.created_by and not self.created_by.is_superuser:
            if self.branch != self.created_by.branch:
                raise ValidationError(_('لا يمكنك إضافة تركيبات لفرع آخر'))

class TransportRequest(models.Model):
    """
    Model for transport requests
    """
    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('scheduled', _('تم الجدولة')),
        ('in_progress', _('قيد التنفيذ')),
        ('completed', _('مكتمل')),
        ('cancelled', _('ملغي')),
    ]
    team_leader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lead_transports',
        verbose_name=_('قائد الفريق')
    )

    
    installation = models.ForeignKey(
        Installation,
        on_delete=models.CASCADE,
        related_name='transport_requests',
        verbose_name=_('طلب التركيب')
    )
    from_location = models.TextField(
        _('من موقع')
    )
    to_location = models.TextField(
        _('إلى موقع')
    )
    scheduled_date = models.DateTimeField(
        _('موعد النقل'),
        null=True,
        blank=True
    )
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_transports',
        verbose_name=_('السائق المسؤول')
    )
    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_transports',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    created_at = models.DateTimeField(
        _('تاريخ الإنشاء'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('تاريخ التحديث'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('طلب نقل')
        verbose_name_plural = _('طلبات النقل')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{_('نقل')} #{self.id} - {self.installation.customer.name}"
