from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
# from django.utils import timezone
from .models import Order, OrderItem, Payment, OrderStatusLog
from .extended_models import ExtendedOrder, AccessoryItem, FabricOrder

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('total_price',)

    def get_formset(self, request, obj=None, **kwargs):
        """Override to make sure we don't try to create inline items for unsaved objects"""
        if obj is None:  # obj is None when we're adding a new object
            self.extra = 0  # Don't show any extra forms for new objects
        else:
            self.extra = 1  # Show extra forms for existing objects
        return super().get_formset(request, obj, **kwargs)

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    readonly_fields = ('payment_date',)

    def get_formset(self, request, obj=None, **kwargs):
        """Override to make sure we don't try to create inline items for unsaved objects"""
        if obj is None:  # obj is None when we're adding a new object
            self.extra = 0  # Don't show any extra forms for new objects
        else:
            self.extra = 1  # Show extra forms for existing objects
        return super().get_formset(request, obj, **kwargs)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'tracking_status', 'final_price', 'payment_status', 'created_at')
    list_filter = (
        'tracking_status',
        'payment_verified',
        'delivery_type',
    )
    search_fields = ('order_number', 'customer__name', 'invoice_number')
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = (
        'created_at',
        'updated_at',
        'order_date',
        'modified_at',
    )

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('customer', 'order_number', 'tracking_status')
        }),
        (_('معلومات التسليم'), {
            'fields': ('delivery_type', 'delivery_address')
        }),
        (_('معلومات مالية'), {
            'fields': ('paid_amount', 'payment_verified')
        }),
        (_('معلومات السعر'), {
            'fields': (
                'final_price',
                'modified_at'
            )
        }),
        (_('معلومات إضافية'), {
            'fields': ('notes',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at', 'order_date', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def payment_status(self, obj):
        if obj.is_fully_paid:
            return format_html('<span style="color: green;">مدفوع بالكامل</span>')
        elif obj.paid_amount > 0:
            return format_html('<span style="color: orange;">مدفوع جزئياً</span>')
        return format_html('<span style="color: red;">غير مدفوع</span>')
    payment_status.short_description = 'حالة الدفع'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

class AccessoryItemInline(admin.TabularInline):
    model = AccessoryItem
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        """Override to make sure we don't try to create inline items for unsaved objects"""
        if obj is None:  # obj is None when we're adding a new object
            self.extra = 0  # Don't show any extra forms for new objects
        else:
            self.extra = 1  # Show extra forms for existing objects
        return super().get_formset(request, obj, **kwargs)

@admin.register(ExtendedOrder)
class ExtendedOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'order_type', 'get_subtype_display', 'branch')
    list_filter = ('order_type', 'goods_type', 'service_type', 'branch')
    search_fields = ('order__order_number', 'invoice_number', 'contract_number')
    inlines = [AccessoryItemInline]
    fieldsets = (
        (_('الطلب الأساسي'), {
            'fields': ('order', 'branch')
        }),
        (_('نوع الطلب'), {
            'fields': ('order_type', 'goods_type', 'service_type')
        }),
        (_('معلومات إضافية'), {
            'fields': ('invoice_number', 'contract_number', 'payment_verified')
        }),
    )

    def get_subtype_display(self, obj):
        if obj.order_type == 'goods':
            return obj.get_goods_type_display() if obj.goods_type else '-'
        elif obj.order_type == 'services':
            return obj.get_service_type_display() if obj.service_type else '-'
        return '-'
    get_subtype_display.short_description = _('النوع الفرعي')

@admin.register(FabricOrder)
class FabricOrderAdmin(admin.ModelAdmin):
    list_display = ('extended_order', 'fabric_type', 'quantity', 'status', 'sent_to_warehouse', 'cutting_completed')
    list_filter = ('status', 'sent_to_warehouse', 'cutting_completed')
    search_fields = ('extended_order__order__order_number', 'fabric_type__name', 'notes')
    fieldsets = (
        (_('معلومات الطلب'), {
            'fields': ('extended_order', 'fabric_type', 'quantity')
        }),
        (_('حالة التقطيع'), {
            'fields': ('status', 'sent_to_warehouse', 'cutting_completed')
        }),
        (_('ملاحظات'), {
            'fields': ('notes',)
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_method', 'payment_date', 'reference_number')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('order__order_number', 'reference_number', 'notes')
    date_hierarchy = 'payment_date'
    fieldsets = (
        (_('معلومات الدفع'), {
            'fields': ('order', 'amount', 'payment_method', 'reference_number')
        }),
        (_('ملاحظات'), {
            'fields': ('notes',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('old_status', 'new_status', 'created_at')
    search_fields = ('order__order_number', 'notes')
    readonly_fields = ('order', 'old_status', 'new_status', 'changed_by', 'created_at')


