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
        ('g', _('جرام')),
        ('ton', _('طن')),
        ('liter', _('لتر')),
        ('ml', _('ملليلتر')),
        ('pack', _('علبة')),
        ('box', _('صندوق')),
        ('gallon', _('جالون')),
        ('dozen', _('دزينة')),
        ('ft', _('قدم')),
        ('yd', _('ياردة')),
        ('cm', _('سنتيمتر')),
        ('mm', _('ملليمتر')),
        ('bag', _('كيس')),
        ('carton', _('كرتون')),
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
        return self.name
    
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

def create_default_stock_transaction_reasons():
    from django.db.utils import IntegrityError
    default_reasons = [
        {'name': 'شراء', 'notes': 'إضافة مخزون نتيجة شراء'},
        {'name': 'بيع', 'notes': 'صرف مخزون نتيجة بيع'},
        {'name': 'إرجاع مورد', 'notes': 'إرجاع مخزون للمورد'},
        {'name': 'إرجاع عميل', 'notes': 'إرجاع مخزون من العميل'},
        {'name': 'تلف', 'notes': 'صرف مخزون نتيجة تلف'},
        {'name': 'جرد', 'notes': 'تسوية نتيجة جرد'},
        {'name': 'هدية', 'notes': 'صرف مخزون كهدية'},
        {'name': 'تعديل رصيد', 'notes': 'تسوية تعديل رصيد يدوي'},
        {'name': 'تحويل', 'notes': 'تحويل مخزون بين المخازن'},
        {'name': 'استهلاك داخلي', 'notes': 'صرف مخزون للاستهلاك الداخلي'},
    ]
    from .models import StockTransactionReason
    for reason in default_reasons:
        try:
            StockTransactionReason.objects.get_or_create(name=reason['name'], defaults={'notes': reason['notes']})
        except IntegrityError:
            continue

class StockTransactionReason(models.Model):
    """
    Model for custom stock transaction reasons
    """
    name = models.CharField(_('اسم السبب'), max_length=100, unique=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('سبب حركة مخزون')
        verbose_name_plural = _('أسباب حركة المخزون')
        ordering = ['name']

    def __str__(self):
        return self.name

class StockTransaction(models.Model):
    """
    Model for tracking stock movements
    """
    TRANSACTION_TYPES = [
        ('in', _('وارد')),
        ('out', _('صادر')),
        ('transfer', _('تحويل')),
        ('adjustment', _('تسوية')),
        ('return', _('إرجاع')),
        ('damage', _('تلف')),
    ]
    STATUS_CHOICES = [
        ('pending', _('بانتظار القبول')),
        ('accepted', _('مقبول')),
        ('rejected', _('مرفوض')),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_transactions',
        verbose_name=_('المنتج')
    )
    transaction_type = models.CharField(
        _('نوع الحركة'),
        max_length=15,
        choices=TRANSACTION_TYPES
    )
    reason = models.ForeignKey(
        StockTransactionReason,
        on_delete=models.PROTECT,
        verbose_name=_('السبب'),
        related_name='transactions',
    )
    quantity = models.PositiveIntegerField(_('الكمية'))
    date = models.DateTimeField(_('التاريخ'), auto_now_add=True)
    reference = models.CharField(_('المرجع'), max_length=100, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)
    warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.PROTECT,
        related_name='stock_transactions',
        verbose_name=_('المخزن'),
        null=False,
        blank=False
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_transactions',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    transfer_permission_number = models.CharField(_('رقم إذن التحويل'), max_length=50, blank=True)
    actual_transfer_date = models.DateTimeField(_('تاريخ التحويل الفعلي'), null=True, blank=True)
    invoice_contract_number = models.CharField(_('رقم الفاتورة/العقد'), max_length=50, blank=True)
    transfer_party = models.CharField(_('جهة التحويل'), max_length=100, blank=True)
    status = models.CharField(_('حالة الحركة'), max_length=15, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        verbose_name = _('حركة مخزون')
        verbose_name_plural = _('حركات المخزون')
        ordering = ['-date']
    
    def __str__(self):
        # تجنب الخطأ إذا لم يكن هناك منتج مرتبط
        try:
            product_name = self.product.name
        except Exception:
            product_name = 'بدون منتج'
        return f"{self.get_transaction_type_display()} - {product_name} - {self.quantity}"

    def clean(self):
        """Validate stock transaction"""
        product = getattr(self, 'product', None)
        if not product:
            return
        if self.transaction_type == 'out' and self.quantity > product.current_stock:
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
        return self.name

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
        return self.name

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

# --- SupplyOrder and SupplyOrderItem ---

# --- Audit Log for Operations ---
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', _('إنشاء')),
        ('update', _('تعديل')),
        ('delete', _('حذف')),
        ('view', _('عرض')),
        ('other', _('أخرى')),
    ]
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='audit_logs', verbose_name=_('المستخدم'))
    action = models.CharField(_('الإجراء'), max_length=20, choices=ACTION_CHOICES)
    object_type = models.CharField(_('نوع الكائن'), max_length=50)
    object_id = models.CharField(_('معرف الكائن'), max_length=100)
    description = models.TextField(_('الوصف'), blank=True)
    timestamp = models.DateTimeField(_('التاريخ والوقت'), auto_now_add=True)

    class Meta:
        verbose_name = _('سجل تدقيق')
        verbose_name_plural = _('سجلات التدقيق')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} - {self.object_type} ({self.object_id}) by {self.user}" if self.user else f"{self.get_action_display()} - {self.object_type} ({self.object_id})"

# --- CustomerOrder and CustomerOrderItem ---
class CustomerOrder(models.Model):
    STATUS_CHOICES = [
        ('new', _('جديد')),
        ('processing', _('قيد المعالجة')),
        ('completed', _('مكتمل')),
        ('cancelled', _('ملغي')),
    ]
    order_number = models.CharField(_('رقم طلب العميل'), max_length=50, unique=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('العميل'))
    order_date = models.DateTimeField(_('تاريخ الطلب'), auto_now_add=True)
    status = models.CharField(_('حالة الطلب'), max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='created_customer_orders', verbose_name=_('تم الإنشاء بواسطة'))
    verbose_name = _('طلب عميل')
    verbose_name_plural = _('طلبات العملاء')
    ordering = ['-order_date']

    def __str__(self):
        return f"{self.order_number} - {self.customer}"

class CustomerOrderItem(models.Model):
    customer_order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='items', verbose_name=_('طلب العميل'))
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name=_('الصنف'))
    quantity = models.PositiveIntegerField(_('الكمية'))
    notes = models.TextField(_('ملاحظات'), blank=True)
    verbose_name = _('عنصر طلب عميل')
    verbose_name_plural = _('عناصر طلبات العملاء')

    def __str__(self):
        return f"{self.product} - {self.quantity}"
class SupplyOrder(models.Model):
    ORDER_TYPE_CHOICES = [
        ('purchase', _('توريد من مورد')),
        ('customer', _('توريد لعميل')),
        ('transfer', _('تحويل بين مخازن')),
    ]
    order_type = models.CharField(_('نوع الطلب'), choices=ORDER_TYPE_CHOICES, max_length=20)
    order_number = models.CharField(_('رقم الطلب/الإذن'), max_length=50, unique=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    actual_transfer_date = models.DateTimeField(_('تاريخ التحويل الفعلي'), null=True, blank=True)
    from_warehouse = models.ForeignKey('Warehouse', null=True, blank=True, related_name='outgoing_supply_orders', on_delete=models.SET_NULL, verbose_name=_('المخزن المصدر'))
    to_warehouse = models.ForeignKey('Warehouse', null=True, blank=True, related_name='incoming_supply_orders', on_delete=models.SET_NULL, verbose_name=_('المخزن المستلم'))
    supplier = models.ForeignKey('Supplier', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('المورد'))
    customer = models.ForeignKey('customers.Customer', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('العميل'))
    customer_invoice_number = models.CharField(_('رقم فاتورة العميل'), max_length=50, blank=True)
    contract_number = models.CharField(_('رقم العقد'), max_length=50, blank=True)
    status = models.CharField(_('الحالة'), max_length=20, choices=[('pending', _('بانتظار التنفيذ')), ('accepted', _('مكتمل')), ('rejected', _('مرفوض'))], default='pending')
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='created_supply_orders', verbose_name=_('تم الإنشاء بواسطة'))

    class Meta:
        verbose_name = _('طلب التوريد')
        verbose_name_plural = _('طلبات التوريد')
        ordering = ['-created_at']
        permissions = [
            ("can_execute_supplyorder", "يمكنه تنفيذ طلبات التوريد")
        ]

    def __str__(self):
        return f"{self.get_order_type_display()} #{self.order_number}"

class SupplyOrderItem(models.Model):
    supply_order = models.ForeignKey(SupplyOrder, on_delete=models.CASCADE, related_name='items', verbose_name=_('طلب التوريد'))
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name=_('الصنف'))
    quantity = models.PositiveIntegerField(_('الكمية'))
    delivered_quantity = models.PositiveIntegerField(_('الكمية المستلمة/المسلمة'), default=0)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('عنصر طلب توريد')
        verbose_name_plural = _('عناصر طلبات التوريد')

    def __str__(self):
        return f"{self.product} ({self.quantity})"
