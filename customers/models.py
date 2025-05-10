from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import Branch

User = get_user_model()

class CustomerCategory(models.Model):
    name = models.CharField(_('اسم التصنيف'), max_length=50, db_index=True)
    description = models.TextField(_('وصف التصنيف'), blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('تصنيف العملاء')
        verbose_name_plural = _('تصنيفات العملاء')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='customer_cat_name_idx'),
        ]

    def __str__(self):
        return self.name

class CustomerNote(models.Model):
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE,
        related_name='notes_history',
        verbose_name=_('العميل')
    )
    note = models.TextField(_('الملاحظة'))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='customer_notes_created',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('ملاحظة العميل')
        verbose_name_plural = _('ملاحظات العملاء')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'created_at'], name='customer_note_idx'),
            models.Index(fields=['created_by'], name='customer_note_creator_idx'),
        ]

    def __str__(self):
        return f"{self.customer.name} - {self.created_at.strftime('%Y-%m-%d')}"

class Customer(models.Model):
    STATUS_CHOICES = [
        ('active', _('نشط')),
        ('inactive', _('غير نشط')),
        ('blocked', _('محظور')),
    ]

    CUSTOMER_TYPE_CHOICES = [
        ('retail', _('أفراد')),
        ('wholesale', _('جملة')),
        ('corporate', _('شركات')),
    ]

    code = models.CharField(_('كود العميل'), max_length=10, unique=True, blank=True)
    image = models.ImageField(
        _('صورة العميل'),
        upload_to='customers/images/%Y/%m/',
        blank=True,
        null=True
    )
    category = models.ForeignKey(
        CustomerCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name=_('تصنيف العميل')
    )
    customer_type = models.CharField(
        _('نوع العميل'),
        max_length=10,
        choices=CUSTOMER_TYPE_CHOICES,
        default='retail'
    )
    name = models.CharField(_('اسم العميل'), max_length=200, db_index=True)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name='customers',
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )
    phone = models.CharField(_('رقم الهاتف'), max_length=20, db_index=True)
    email = models.EmailField(_('البريد الإلكتروني'), blank=True, null=True)
    address = models.TextField(_('العنوان'))
    status = models.CharField(
        _('الحالة'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='customers_created',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('عميل')
        verbose_name_plural = _('سجل العملاء')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name'], name='customer_name_idx'),
            models.Index(fields=['phone'], name='customer_phone_idx'),
            models.Index(fields=['status'], name='customer_status_idx'),
            models.Index(fields=['customer_type'], name='customer_type_idx'),
            models.Index(fields=['branch', 'status'], name='customer_branch_status_idx'),
            models.Index(fields=['created_at'], name='customer_created_at_idx'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        # Only allow users to create customers in their branch
        if self.created_by and not self.created_by.is_superuser:
            if self.branch != self.created_by.branch:
                raise ValidationError(_('لا يمكنك إضافة عملاء لفرع آخر'))

    def save(self, *args, **kwargs):
        if not self.code:
            # Get the latest customer code for this branch
            latest_customer = Customer.objects.filter(
                branch=self.branch
            ).order_by('-code').first()

            if latest_customer:
                # Extract the sequence number and increment
                try:
                    sequence = int(latest_customer.code.split('-')[1]) + 1
                except (IndexError, ValueError):
                    sequence = 1
            else:
                sequence = 1

            # Generate new code in format '001-0001'
            self.code = f"{self.branch.code}-{str(sequence).zfill(4)}"
        
        super().save(*args, **kwargs)

    @property
    def branch_code(self):
        """Get the branch code part"""
        return self.code.split('-')[0] if self.code else ''

    @property
    def sequence_number(self):
        """Get the sequence number part"""
        return self.code.split('-')[1] if self.code else ''
