from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Category, Product, StockTransaction, Supplier, PurchaseOrder, PurchaseOrderItem,
    Warehouse, WarehouseLocation, ProductBatch, InventoryAdjustment, StockAlert
)
from data_import_export.admin import AdminMultiSheetImportExportMixin

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name', 'description')

@admin.register(Product)
class ProductAdmin(AdminMultiSheetImportExportMixin, admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'price', 'current_stock', 'needs_restock')
    list_filter = ('category', 'unit', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('current_stock', 'created_at', 'updated_at')
    
    fieldsets = (
        (_('معلومات المنتج'), {
            'fields': ('name', 'code', 'category', 'description')
        }),
        (_('التفاصيل'), {
            'fields': ('unit', 'price', 'minimum_stock')
        }),
        (_('معلومات المخزون'), {
            'fields': ('current_stock', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'reason', 'quantity', 'date')
    list_filter = ('transaction_type', 'reason', 'date')
    search_fields = ('product__name', 'reference', 'notes')
    readonly_fields = ('date', 'created_by')
    
    fieldsets = (
        (_('معلومات الحركة'), {
            'fields': ('product', 'transaction_type', 'reason', 'quantity')
        }),
        (_('التفاصيل'), {
            'fields': ('reference', 'notes')
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'date'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Supplier)
class SupplierAdmin(AdminMultiSheetImportExportMixin, admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'phone', 'email', 'address')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(AdminMultiSheetImportExportMixin, admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'status', 'order_date', 'total_amount')
    list_filter = ('status', 'order_date')
    search_fields = ('order_number', 'supplier__name', 'notes')
    readonly_fields = ('order_date', 'created_by')
    
    fieldsets = (
        (_('معلومات طلب الشراء'), {
            'fields': ('order_number', 'supplier', 'warehouse', 'status')
        }),
        (_('التواريخ'), {
            'fields': ('expected_date',)
        }),
        (_('المعلومات المالية'), {
            'fields': ('total_amount',)
        }),
        (_('ملاحظات إضافية'), {
            'fields': ('notes',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity', 'unit_price', 'received_quantity')
    list_filter = ('purchase_order__status',)
    search_fields = ('purchase_order__order_number', 'product__name')

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'branch', 'manager', 'is_active')
    list_filter = ('branch', 'is_active')
    search_fields = ('name', 'code', 'address')

@admin.register(WarehouseLocation)
class WarehouseLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'warehouse')
    list_filter = ('warehouse',)
    search_fields = ('name', 'code', 'description')

@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch_number', 'location', 'quantity', 'expiry_date')
    list_filter = ('location__warehouse', 'manufacturing_date', 'expiry_date')
    search_fields = ('product__name', 'batch_number', 'barcode')
    readonly_fields = ('barcode', 'created_at')

@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('product', 'adjustment_type', 'quantity_before', 'quantity_after', 'date')
    list_filter = ('adjustment_type', 'date')
    search_fields = ('product__name', 'reason')
    readonly_fields = ('date', 'created_by')

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('product', 'alert_type', 'status', 'created_at')
    list_filter = ('alert_type', 'status', 'created_at')
    search_fields = ('product__name', 'message')
    readonly_fields = ('created_at', 'resolved_at', 'resolved_by')
