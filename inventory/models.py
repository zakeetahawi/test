from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from accounts.models import User, Branch
import uuid
from datetime import datetime

class Category(models.Model):
    """
    Model for product categories
    """
    name = models.CharField(_('اسم الفئة'), max_length=100)
    description = models.TextField(_('الوصف'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('الفئة الأب')
    )
    
    class Meta:
        verbose_name = _('فئة')
        verbose_name_plural = _('الفئات')
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name

class Product(models.Model):
    """
    Model for products
    """
    UNIT_CHOICES = [
        ('piece', _('قطعة')),
        ('meter', _('متر')),
        ('sqm', _('متر مربع')),
        ('kg', _('كيلوجرام')),
    ]
    
    name = models.CharField(_('اسم المنتج'), max_length=200)
    code = models.CharField(_('كود المنتج'), max_length=50, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        verbose_name=_('الفئة')
    )
    description = models.TextField(_('الوصف'), blank=True)
    unit = models.CharField(
        _('وحدة القياس'),
        max_length=10,
        choices=UNIT_CHOICES,
        default='piece'
    )
    price = models.DecimalField(
        _('السعر'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    minimum_stock = models.PositiveIntegerField(
        _('الحد الأدنى للمخزون'),
        default=0
    )
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('منتج')
        verbose_name_plural = _('المنتجات')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def current_stock(self):
        """Get current stock level"""
        stock_ins = sum(transaction.quantity for transaction in 
                       self.stock_transactions.filter(transaction_type='in'))
        stock_outs = sum(transaction.quantity for transaction in 
                        self.stock_transactions.filter(transaction_type='out'))
        return stock_ins - stock_outs
    
    @property
    def needs_restock(self):
        """Check if product needs restocking"""
        return self.current_stock <= self.minimum_stock

class StockTransaction(models.Model):
    """
    Model for tracking stock movements
    """
    TRANSACTION_TYPES = [
        ('in', _('وارد')),
        ('out', _('صادر')),
    ]
    
    TRANSACTION_REASONS = [
        ('purchase', _('شراء')),
        ('sale', _('بيع')),
        ('return', _('مرتجع')),
        ('damage', _('تالف')),
        ('adjustment', _('تسوية')),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_transactions',
        verbose_name=_('المنتج')
    )
    transaction_type = models.CharField(
        _('نوع الحركة'),
        max_length=3,
        choices=TRANSACTION_TYPES
    )
    reason = models.CharField(
        _('السبب'),
        max_length=20,
        choices=TRANSACTION_REASONS
    )
    quantity = models.PositiveIntegerField(_('الكمية'))
    date = models.DateTimeField(_('التاريخ'), auto_now_add=True)
    reference = models.CharField(_('المرجع'), max_length=100, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_transactions',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    
    class Meta:
        verbose_name = _('حركة مخزون')
        verbose_name_plural = _('حركات المخزون')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} - {self.quantity}"
    
    def clean(self):
        """Validate stock transaction"""
        if self.transaction_type == 'out' and self.quantity > self.product.current_stock:
            raise ValidationError(_('الكمية المطلوبة غير متوفرة في المخزون'))

class Supplier(models.Model):
    """
    Model for suppliers
    """
    name = models.CharField(_('اسم المورد'), max_length=200)
    contact_person = models.CharField(_('الشخص المسؤول'), max_length=100)
    phone = models.CharField(_('رقم الهاتف'), max_length=20)
    email = models.EmailField(_('البريد الإلكتروني'), blank=True)
    address = models.TextField(_('العنوان'))
    tax_number = models.CharField(_('الرقم الضريبي'), max_length=50, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)
    
    class Meta:
        verbose_name = _('مورد')
        verbose_name_plural = _('الموردين')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Warehouse(models.Model):
    """
    Model for warehouses
    """
    name = models.CharField(_('اسم المخزن'), max_length=100)
    code = models.CharField(_('كود المخزن'), max_length=20, unique=True)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='warehouses',
        verbose_name=_('الفرع')
    )
    address = models.TextField(_('العنوان'), blank=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_warehouses',
        verbose_name=_('المدير المسؤول')
    )
    is_active = models.BooleanField(_('نشط'), default=True)
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('مخزن')
        verbose_name_plural = _('المخازن')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class WarehouseLocation(models.Model):
    """
    Model for warehouse locations (shelves, racks, etc.)
    """
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name=_('المخزن')
    )
    name = models.CharField(_('اسم الموقع'), max_length=100)
    code = models.CharField(_('كود الموقع'), max_length=20)
    description = models.TextField(_('الوصف'), blank=True)
    
    class Meta:
        verbose_name = _('موقع في المخزن')
        verbose_name_plural = _('مواقع المخزن')
        ordering = ['warehouse', 'name']
        unique_together = ['warehouse', 'code']
    
    def __str__(self):
        return f"{self.warehouse.name} - {self.name} ({self.code})"

class ProductBatch(models.Model):
    """
    Model for tracking product batches
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('المنتج')
    )
    batch_number = models.CharField(_('رقم الدفعة'), max_length=50)
    location = models.ForeignKey(
        WarehouseLocation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='product_batches',
        verbose_name=_('الموقع')
    )
    quantity = models.PositiveIntegerField(_('الكمية'))
    manufacturing_date = models.DateField(_('تاريخ التصنيع'), null=True, blank=True)
    expiry_date = models.DateField(_('تاريخ انتهاء الصلاحية'), null=True, blank=True)
    cost_price = models.DecimalField(_('سعر التكلفة'), max_digits=10, decimal_places=2)
    barcode = models.CharField(_('الباركود'), max_length=100, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('دفعة منتج')
        verbose_name_plural = _('دفعات المنتجات')
        ordering = ['-created_at']
        unique_together = ['product', 'batch_number']
    
    def __str__(self):
        return f"{self.product.name} - {self.batch_number}"
    
    def save(self, *args, **kwargs):
        # Generate barcode if not provided
        if not self.barcode:
            self.barcode = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class InventoryAdjustment(models.Model):
    """
    Model for inventory adjustments
    """
    ADJUSTMENT_TYPES = [
        ('count', _('جرد')),
        ('damage', _('تلف')),
        ('loss', _('فقدان')),
        ('return', _('مرتجع')),
        ('other', _('أخرى')),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='adjustments',
        verbose_name=_('المنتج')
    )
    batch = models.ForeignKey(
        ProductBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adjustments',
        verbose_name=_('الدفعة')
    )
    adjustment_type = models.CharField(
        _('نوع التسوية'),
        max_length=10,
        choices=ADJUSTMENT_TYPES
    )
    quantity_before = models.PositiveIntegerField(_('الكمية قبل التسوية'))
    quantity_after = models.PositiveIntegerField(_('الكمية بعد التسوية'))
    reason = models.TextField(_('سبب التسوية'))
    date = models.DateTimeField(_('تاريخ التسوية'), auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventory_adjustments',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    
    class Meta:
        verbose_name = _('تسوية مخزون')
        verbose_name_plural = _('تسويات المخزون')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.get_adjustment_type_display()} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Create stock transaction for the adjustment
        adjustment_quantity = self.quantity_after - self.quantity_before
        transaction_type = 'in' if adjustment_quantity > 0 else 'out'
        
        super().save(*args, **kwargs)
        
        # Create stock transaction after saving
        if adjustment_quantity != 0:
            StockTransaction.objects.create(
                product=self.product,
                transaction_type=transaction_type,
                reason='adjustment',
                quantity=abs(adjustment_quantity),
                reference=f"ADJ-{self.id}",
                notes=self.reason,
                created_by=self.created_by
            )

class StockAlert(models.Model):
    """
    Model for stock alerts
    """
    ALERT_TYPES = [
        ('low_stock', _('مخزون منخفض')),
        ('out_of_stock', _('نفاد المخزون')),
        ('expiry', _('قرب انتهاء الصلاحية')),
    ]
    
    STATUS_CHOICES = [
        ('new', _('جديد')),
        ('in_progress', _('قيد المعالجة')),
        ('resolved', _('تم الحل')),
        ('ignored', _('تم التجاهل')),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        verbose_name=_('المنتج')
    )
    alert_type = models.CharField(
        _('نوع التنبيه'),
        max_length=20,
        choices=ALERT_TYPES
    )
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    message = models.TextField(_('رسالة التنبيه'))
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    resolved_at = models.DateTimeField(_('تاريخ الحل'), null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_stock_alerts',
        verbose_name=_('تم الحل بواسطة')
    )
    
    class Meta:
        verbose_name = _('تنبيه مخزون')
        verbose_name_plural = _('تنبيهات المخزون')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.product.name}"

class PurchaseOrder(models.Model):
    """
    Model for purchase orders
    """
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('ordered', _('تم الطلب')),
        ('received', _('تم الاستلام')),
        ('cancelled', _('ملغي')),
    ]
    
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='purchase_orders',
        verbose_name=_('المورد')
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_orders',
        verbose_name=_('المخزن المستلم')
    )
    order_number = models.CharField(_('رقم الطلب'), max_length=50, unique=True)
    order_date = models.DateTimeField(_('تاريخ الطلب'), auto_now_add=True)
    expected_date = models.DateField(_('تاريخ التوريد المتوقع'), null=True, blank=True)
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    total_amount = models.DecimalField(
        _('المبلغ الإجمالي'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_orders_created',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    
    class Meta:
        verbose_name = _('طلب شراء')
        verbose_name_plural = _('طلبات الشراء')
        ordering = ['-order_date']
    
    def __str__(self):
        return f"{self.order_number} - {self.supplier.name}"

class PurchaseOrderItem(models.Model):
    """
    Model for purchase order items
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('طلب الشراء')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='purchase_order_items',
        verbose_name=_('المنتج')
    )
    quantity = models.PositiveIntegerField(_('الكمية'))
    unit_price = models.DecimalField(
        _('سعر الوحدة'),
        max_digits=10,
        decimal_places=2
    )
    received_quantity = models.PositiveIntegerField(_('الكمية المستلمة'), default=0)
    notes = models.TextField(_('ملاحظات'), blank=True)
    
    class Meta:
        verbose_name = _('عنصر طلب شراء')
        verbose_name_plural = _('عناصر طلبات الشراء')
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    @property
    def is_fully_received(self):
        return self.received_quantity >= self.quantity
