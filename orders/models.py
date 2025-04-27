import json
from django.db import models
from django.conf import settings
from customers.models import Customer
from inventory.models import Product

class Salesperson(models.Model):
    name = models.CharField(max_length=100, verbose_name='اسم البائع')
    branch = models.ForeignKey('accounts.Branch', on_delete=models.CASCADE, related_name='salespersons', verbose_name='الفرع')
    
    class Meta:
        verbose_name = 'بائع'
        verbose_name_plural = 'البائعون'
        unique_together = ('name', 'branch')
    
    def __str__(self):
        return f'{self.name} - {self.branch}'

class Order(models.Model):
    STATUS_CHOICES = [
        ('normal', 'عادي'),
        ('vip', 'VIP'),
    ]
    
    ORDER_TYPES = [
        ('fabric', 'قماش'),
        ('accessory', 'إكسسوار'),
        ('installation', 'تركيب'),
        ('inspection', 'معاينة'),
        ('transport', 'نقل'),
        ('tailoring', 'تفصيل'),
    ]

    TRACKING_STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('processing', 'قيد المعالجة'),
        ('warehouse', 'في المستودع'),
        ('factory', 'في المصنع'),
        ('cutting', 'قيد القص'),
        ('ready', 'جاهز للتسليم'),
        ('delivered', 'تم التسليم'),
    ]

    DELIVERY_TYPE_CHOICES = [
        ('home', 'توصيل للمنزل'),
        ('branch', 'استلام من الفرع'),
    ]

    ITEM_TYPE_CHOICES = [
        ('fabric', 'قماش'),
        ('accessory', 'إكسسوار'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_orders', verbose_name='العميل')
    salesperson = models.ForeignKey('Salesperson', on_delete=models.PROTECT, related_name='orders', verbose_name='البائع', null=True, blank=True)
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_TYPE_CHOICES, default='branch', verbose_name='نوع التسليم')
    delivery_address = models.TextField(blank=True, null=True, verbose_name='عنوان التسليم')
    order_number = models.CharField(max_length=50, unique=True, verbose_name='رقم الطلب')
    order_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطلب')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal', verbose_name='حالة الطلب')

    # Order type fields
    selected_types = models.JSONField(default=list, verbose_name='أنواع الطلب المختارة')
    # Keep old fields for backward compatibility
    order_type = models.CharField(max_length=10, choices=[('product', 'منتج'), ('service', 'خدمة')], null=True, blank=True)
    service_types = models.JSONField(default=list, blank=True, verbose_name='أنواع الخدمات')
    tracking_status = models.CharField(
        max_length=20,
        choices=TRACKING_STATUS_CHOICES,
        default='pending',
        verbose_name='حالة التتبع'
    )
    last_notification_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ آخر إشعار')
    invoice_number = models.CharField(max_length=50, null=True, blank=True, verbose_name='رقم الفاتورة')
    contract_number = models.CharField(max_length=50, null=True, blank=True, verbose_name='رقم العقد')
    payment_verified = models.BooleanField(default=False, verbose_name='تم التحقق من السداد')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='المبلغ الإجمالي')
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='المبلغ المدفوع')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='تم الإنشاء بواسطة')
    branch = models.ForeignKey('accounts.Branch', on_delete=models.CASCADE, related_name='orders', verbose_name='الفرع', null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Get the last order number for this customer
            last_order = Order.objects.filter(
                customer=self.customer
            ).order_by('-order_number').first()
            
            if last_order:
                # Extract the number part and increment it
                try:
                    last_num = int(last_order.order_number.split('-')[-1])
                    next_num = last_num + 1
                except ValueError:
                    next_num = 1
            else:
                next_num = 1
            
            # Generate new order number
            self.order_number = f"{self.customer.code}-{next_num:04d}"
        
        # Validate selected types
        selected_types = self.selected_types or []
        if isinstance(selected_types, str):
            try:
                selected_types = json.loads(selected_types)
            except json.JSONDecodeError:
                selected_types = [st.strip() for st in selected_types.split(',') if st.strip()]
        
        if not selected_types:
            raise models.ValidationError('يجب اختيار نوع طلب واحد على الأقل')

        # Contract number validation
        if 'tailoring' in selected_types and not self.contract_number:
            raise models.ValidationError('رقم العقد مطلوب لخدمة التفصيل')

        # Invoice number validation - required for all types except inspection alone
        if not (len(selected_types) == 1 and selected_types[0] == 'inspection'):
            if not self.invoice_number:
                raise models.ValidationError('رقم الفاتورة مطلوب')

        # Set legacy fields for backward compatibility
        has_products = any(t in ['fabric', 'accessory'] for t in selected_types)
        has_services = any(t in ['installation', 'inspection', 'transport', 'tailoring'] for t in selected_types)
        
        if has_products:
            self.order_type = 'product'
        if has_services:
            self.order_type = 'service'
            self.service_types = [t for t in selected_types if t in ['installation', 'inspection', 'transport', 'tailoring']]
        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.order_number} - {self.customer.name}'

    @property
    def remaining_amount(self):
        """Calculate remaining amount to be paid"""
        return self.total_amount - self.paid_amount

    @property
    def is_fully_paid(self):
        """Check if order is fully paid"""
        return self.paid_amount >= self.total_amount

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='الطلب')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items', verbose_name='المنتج')
    quantity = models.PositiveIntegerField(verbose_name='الكمية')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='سعر الوحدة')
    item_type = models.CharField(
        max_length=10,
        choices=Order.ITEM_TYPE_CHOICES,
        default='fabric',
        verbose_name='نوع العنصر'
    )
    processing_status = models.CharField(
        max_length=20,
        choices=Order.TRACKING_STATUS_CHOICES,
        default='pending',
        verbose_name='حالة المعالجة'
    )
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'عنصر الطلب'
        verbose_name_plural = 'عناصر الطلب'

    def __str__(self):
        return f'{self.product.name} ({self.quantity})'

    @property
    def total_price(self):
        """Calculate total price for this item"""
        return self.quantity * self.unit_price

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'نقداً'),
        ('bank_transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name='الطلب')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المبلغ')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash', verbose_name='طريقة الدفع')
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الدفع')
    reference_number = models.CharField(max_length=100, blank=True, verbose_name='رقم المرجع')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='تم الإنشاء بواسطة')

    class Meta:
        verbose_name = 'دفعة'
        verbose_name_plural = 'الدفعات'
        ordering = ['-payment_date']

    def __str__(self):
        return f'{self.order.order_number} - {self.amount} ({self.get_payment_method_display()})'

    def save(self, *args, **kwargs):
        """Update order's paid amount when payment is saved"""
        super().save(*args, **kwargs)
        # Update order's paid amount
        total_payments = Payment.objects.filter(order=self.order).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        self.order.paid_amount = total_payments
        self.order.save()
