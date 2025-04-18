from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from accounts.models import User, Branch
from .models import Order
from inventory.models import Product

class ExtendedOrder(models.Model):
    """
    Model to extend the Order model with additional fields for order types
    """
    ORDER_TYPE_CHOICES = [
        ('goods', _('سلع')),
        ('services', _('خدمات')),
    ]
    
    GOODS_TYPE_CHOICES = [
        ('accessories', _('اكسسوار')),
        ('fabric', _('قماش')),
    ]
    
    SERVICE_TYPE_CHOICES = [
        ('inspection', _('معاينة')),
        ('tailoring', _('تفصيل')),
        ('installation', _('تركيب')),
        ('transport', _('نقل')),
    ]
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='extended_info',
        verbose_name=_('الطلب')
    )
    order_type = models.CharField(
        _('نوع الطلب'),
        max_length=10,
        choices=ORDER_TYPE_CHOICES
    )
    goods_type = models.CharField(
        _('نوع السلعة'),
        max_length=15,
        choices=GOODS_TYPE_CHOICES,
        null=True,
        blank=True
    )
    service_type = models.CharField(
        _('نوع الخدمة'),
        max_length=15,
        choices=SERVICE_TYPE_CHOICES,
        null=True,
        blank=True
    )
    invoice_number = models.CharField(
        _('رقم الفاتورة'),
        max_length=50,
        null=True,
        blank=True
    )
    contract_number = models.CharField(
        _('رقم العقد'),
        max_length=50,
        null=True,
        blank=True
    )
    payment_verified = models.BooleanField(
        _('تم التحقق من السداد'),
        default=False
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='extended_orders',
        verbose_name=_('الفرع')
    )
    
    class Meta:
        verbose_name = _('معلومات إضافية للطلب')
        verbose_name_plural = _('معلومات إضافية للطلبات')
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_order_type_display()}"
    
    def clean(self):
        # Validate based on order type
        if self.order_type == 'goods':
            if not self.goods_type:
                raise ValidationError(_('يجب تحديد نوع السلعة'))
            
            # Validate fabric orders
            if self.goods_type == 'fabric' and not self.invoice_number:
                raise ValidationError(_('يجب إدخال رقم الفاتورة لطلبات القماش'))
                
        elif self.order_type == 'services':
            if not self.service_type:
                raise ValidationError(_('يجب تحديد نوع الخدمة'))
            
            # Validate tailoring orders
            if self.service_type == 'tailoring' and (not self.contract_number or not self.invoice_number):
                raise ValidationError(_('يجب إدخال رقم العقد ورقم الفاتورة لطلبات التفصيل'))
            
            # Validate installation orders
            if self.service_type == 'installation' and not self.invoice_number:
                raise ValidationError(_('يجب إدخال رقم الفاتورة لطلبات التركيب'))
        
        # Only allow users to create orders in their branch
        if hasattr(self, 'order') and self.order and hasattr(self.order, 'created_by') and self.order.created_by and not self.order.created_by.is_superuser:
            if self.branch != self.order.created_by.branch:
                raise ValidationError(_('لا يمكنك إضافة طلبات لفرع آخر'))

class AccessoryItem(models.Model):
    """
    Model for accessory items in an order
    """
    extended_order = models.ForeignKey(
        ExtendedOrder,
        on_delete=models.CASCADE,
        related_name='accessory_items',
        verbose_name=_('الطلب')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='accessory_items',
        verbose_name=_('المنتج')
    )
    quantity = models.PositiveIntegerField(
        _('الكمية')
    )
    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('عنصر اكسسوار')
        verbose_name_plural = _('عناصر الاكسسوارات')
    
    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

class FabricOrder(models.Model):
    """
    Model for fabric orders
    """
    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('cutting', _('قيد التقطيع')),
        ('completed', _('مكتمل')),
        ('cancelled', _('ملغي')),
    ]
    
    extended_order = models.OneToOneField(
        ExtendedOrder,
        on_delete=models.CASCADE,
        related_name='fabric_order',
        verbose_name=_('الطلب')
    )
    fabric_type = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='fabric_orders',
        verbose_name=_('نوع القماش')
    )
    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        _('الحالة'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    sent_to_warehouse = models.BooleanField(
        _('تم إرسال للمخزن'),
        default=False
    )
    cutting_completed = models.BooleanField(
        _('تم التقطيع'),
        default=False
    )
    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('طلب قماش')
        verbose_name_plural = _('طلبات الأقمشة')
    
    def __str__(self):
        return f"{self.fabric_type.name} - {self.quantity} {self.fabric_type.get_unit_display()}"
