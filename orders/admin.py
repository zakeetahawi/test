from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem, Payment, Salesperson
from .extended_models import ExtendedOrder, AccessoryItem, FabricOrder
from data_import_export.admin import AdminMultiSheetImportExportMixin

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

@admin.register(Order)
class OrderAdmin(AdminMultiSheetImportExportMixin, admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'total_amount', 'paid_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer__name', 'notes')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = ('created_at', 'updated_at', 'order_date')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('customer', 'order_number', 'status')
        }),
        (_('معلومات مالية'), {
            'fields': ('total_amount', 'paid_amount')
        }),
        (_('ملاحظات'), {
            'fields': ('notes',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at', 'order_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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
