from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from .models import Order, OrderItem, Payment, OrderStatusLog, DynamicPricing, ShippingDetails
from .extended_models import ExtendedOrder, AccessoryItem, FabricOrder
from data_import_export.admin import AdminMultiSheetImportExportMixin

@admin.register(DynamicPricing)
class DynamicPricingAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'discount_percentage', 'is_active', 'priority', 'start_date', 'end_date')
    list_filter = ('rule_type', 'is_active', 'customer_type')
    search_fields = ('name', 'description')
    ordering = ('-priority', '-created_at')
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'rule_type', 'discount_percentage', 'description')
        }),
        ('شروط التطبيق', {
            'fields': ('min_quantity', 'min_amount', 'customer_type', 'start_date', 'end_date')
        }),
        ('الإعدادات', {
            'fields': ('is_active', 'priority')
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            if obj.rule_type != 'quantity':
                form.fields['min_quantity'].widget.attrs['disabled'] = True
            if obj.rule_type != 'special_offer':
                form.fields['min_amount'].widget.attrs['disabled'] = True
            if obj.rule_type != 'customer_type':
                form.fields['customer_type'].widget.attrs['disabled'] = True
        return form

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('total_price',)

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    readonly_fields = ('payment_date',)

@admin.register(Order)
class OrderAdmin(AdminMultiSheetImportExportMixin, admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'tracking_status', 'final_price', 'payment_status', 'created_at')
    list_filter = (
        'tracking_status',
        'payment_verified',
        'delivery_type',
        ('dynamic_pricing_rule', admin.RelatedOnlyFieldListFilter),
        'price_changed',
    )
    search_fields = ('order_number', 'customer__name', 'invoice_number')
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = (
        'created_at',
        'updated_at',
        'order_date',
        'price_changed',
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
        (_('التسعير الديناميكي'), {
            'fields': (
                'dynamic_pricing_rule',
                'final_price',
                'price_changed',
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
        return qs.select_related('dynamic_pricing_rule')

class AccessoryItemInline(admin.TabularInline):
    model = AccessoryItem
    extra = 1

@admin.register(ExtendedOrder)
class ExtendedOrderAdmin(AdminMultiSheetImportExportMixin, admin.ModelAdmin):
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
class FabricOrderAdmin(AdminMultiSheetImportExportMixin, admin.ModelAdmin):
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
class PaymentAdmin(AdminMultiSheetImportExportMixin, admin.ModelAdmin):
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

@admin.register(ShippingDetails)
class ShippingDetailsAdmin(admin.ModelAdmin):
    list_display = ('order', 'shipping_provider', 'shipping_status', 'tracking_number', 'estimated_delivery_date', 'actual_delivery_date')
    list_filter = ('shipping_provider', 'shipping_status')
    search_fields = ('order__order_number', 'tracking_number', 'recipient_name', 'recipient_phone')
    readonly_fields = ('last_update', 'created_at')
    
    fieldsets = (
        (_('معلومات الطلب'), {
            'fields': ('order', 'shipping_provider', 'shipping_status')
        }),
        (_('معلومات التتبع'), {
            'fields': ('tracking_number', 'estimated_delivery_date', 'actual_delivery_date')
        }),
        (_('معلومات المستلم'), {
            'fields': ('recipient_name', 'recipient_phone', 'shipping_notes')
        }),
        (_('معلومات إضافية'), {
            'fields': ('shipping_cost', 'last_update', 'created_at'),
            'classes': ('collapse',)
        }),
    )
