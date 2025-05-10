from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Installation, InstallationTeam, InstallationStep, InstallationQualityCheck, InstallationIssue, InstallationNotification

@admin.register(InstallationTeam)
class InstallationTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader', 'branch', 'is_active')
    list_filter = ('is_active', 'branch')
    search_fields = ('name', 'leader__username')
    filter_horizontal = ('members',)

@admin.register(Installation)
class InstallationAdmin(admin.ModelAdmin):
    list_display = ('order', 'team', 'status', 'scheduled_date', 'quality_rating')
    list_filter = ('status', 'team', 'scheduled_date')
    search_fields = ('order__order_number', 'notes')
    date_hierarchy = 'scheduled_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('order', 'inspection', 'team', 'scheduled_date')
        }),
        (_('حالة التركيب'), {
            'fields': ('status', 'actual_start_date', 'actual_end_date', 'quality_rating')
        }),
        (_('ملاحظات'), {
            'fields': ('notes',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InstallationStep)
class InstallationStepAdmin(admin.ModelAdmin):
    list_display = ('name', 'installation', 'order', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'completed_at')
    search_fields = ('name', 'description', 'installation__order__order_number')

@admin.register(InstallationQualityCheck)
class InstallationQualityCheckAdmin(admin.ModelAdmin):
    list_display = ('installation', 'criteria', 'rating', 'checked_by', 'created_at')
    list_filter = ('criteria', 'rating', 'created_at')
    search_fields = ('installation__order__order_number', 'notes')

@admin.register(InstallationIssue)
class InstallationIssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'installation', 'priority', 'status', 'reported_by')
    list_filter = ('priority', 'status')
    search_fields = ('title', 'description', 'installation__order__order_number')

@admin.register(InstallationNotification)
class InstallationNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'installation', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'installation__order__order_number')
