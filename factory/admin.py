from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ProductionLine, ProductionOrder, ProductionStage, ProductionIssue
from accounts.utils import send_notification
from django.utils import timezone

@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'production_line', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('order__order_number', 'notes')
    readonly_fields = ('created_at', 'created_by')
    
    fieldsets = (
        (_('معلومات أمر الإنتاج'), {
            'fields': ('order', 'production_line', 'status')
        }),
        (_('التواريخ'), {
            'fields': ('start_date', 'end_date', 'estimated_completion')
        }),
        (_('ملاحظات إضافية'), {
            'fields': ('notes',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ProductionStage)
class ProductionStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'production_order', 'start_date', 'end_date', 'completed')
    list_filter = ('completed', 'start_date', 'end_date')
    search_fields = ('name', 'description', 'production_order__order__order_number')
    
    fieldsets = (
        (_('معلومات مرحلة الإنتاج'), {
            'fields': ('production_order', 'name', 'description')
        }),
        (_('التواريخ'), {
            'fields': ('start_date', 'end_date', 'completed')
        }),
        (_('التعيين'), {
            'fields': ('assigned_to', 'notes')
        }),
    )

@admin.register(ProductionIssue)
class ProductionIssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'production_order', 'severity', 'reported_at', 'resolved')
    list_filter = ('severity', 'resolved', 'reported_at')
    search_fields = ('title', 'description', 'production_order__order__order_number')
    readonly_fields = ('reported_at', 'reported_by', 'resolved_at', 'resolved_by')
    
    fieldsets = (
        (_('معلومات المشكلة'), {
            'fields': ('production_order', 'title', 'description', 'severity')
        }),
        (_('حالة المشكلة'), {
            'fields': ('resolved', 'resolution_notes')
        }),
        (_('معلومات النظام'), {
            'fields': ('reported_by', 'reported_at', 'resolved_by', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Set reported_by if this is a new issue
        if not change:
            obj.reported_by = request.user
        
        # If issue is being marked as resolved
        if 'resolved' in form.changed_data and obj.resolved:
            obj.resolved_by = request.user
            obj.resolved_at = timezone.now()
        
        # Save the model
        super().save_model(request, obj, form, change)
        
        # If this is a new issue, update the production order status to stalled
        if not change and obj.production_order.status != 'stalled':
            production_order = obj.production_order
            old_status = production_order.status
            production_order.status = 'stalled'
            production_order.save()
            
            # Send notification to the branch
            if production_order.order.branch:
                send_notification(
                    title=f'تعطل أمر إنتاج #{production_order.id}',
                    message=f'تم تعطل أمر الإنتاج الخاص بالطلب {production_order.order.order_number} بسبب مشكلة: {obj.title}',
                    sender=request.user,
                    sender_department_code='factory',
                    target_department_code='orders',
                    target_branch=production_order.order.branch,
                    priority='high',
                    related_object=production_order
                )
