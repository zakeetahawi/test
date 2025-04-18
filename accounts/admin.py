from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Branch, Department, Notification, CompanyInfo, FormField

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'sender', 'sender_department', 'target_department', 'priority', 'created_at', 'is_read')
    list_filter = ('is_read', 'priority', 'sender_department', 'target_department', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'updated_at', 'read_at', 'read_by')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'message', 'priority')
        }),
        (_('معلومات المرسل'), {
            'fields': ('sender', 'sender_department')
        }),
        (_('معلومات المستلم'), {
            'fields': ('target_department', 'target_branch')
        }),
        (_('الكائن المرتبط'), {
            'fields': ('content_type', 'object_id')
        }),
        (_('حالة الإشعار'), {
            'fields': ('is_read', 'read_at', 'read_by')
        }),
        (_('التواريخ'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'url_name', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    ordering = ['order', 'name']
    prepopulated_fields = {'code': ('name',)}

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'phone', 'email')
    ordering = ['code']

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'branch', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'branch')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('معلومات شخصية'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'branch', 'departments')}),
        (_('الصلاحيات'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('تواريخ مهمة'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'branch', 'departments'),
        }),
    )

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'website')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'logo', 'address', 'phone', 'email', 'website', 'version', 'release_date', 'working_hours')
        }),
        (_('عن النظام'), {
            'fields': ('description',)
        }),
        (_('معلومات قانونية'), {
            'fields': ('tax_number', 'commercial_register')
        }),
        (_('وسائل التواصل الاجتماعي'), {
            'fields': ('facebook', 'twitter', 'instagram', 'linkedin', 'social_links')
        }),
        (_('معلومات إضافية'), {
            'fields': ('about', 'vision', 'mission')
        }),
        (_('إعدادات النظام'), {
            'fields': ('primary_color', 'secondary_color', 'accent_color')
        }),
    )
    
    def has_add_permission(self, request):
        # Check if there's already an instance
        return not CompanyInfo.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the company info
        return False

@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ('form_type', 'field_name', 'field_label', 'field_type', 'required', 'enabled', 'order')
    list_filter = ('form_type', 'field_type', 'required', 'enabled')
    search_fields = ('field_name', 'field_label')
    ordering = ['form_type', 'order']
    
    fieldsets = (
        (_('معلومات الحقل'), {
            'fields': ('form_type', 'field_name', 'field_label', 'field_type', 'required', 'enabled', 'order')
        }),
        (_('خيارات الحقل'), {
            'fields': ('choices', 'default_value', 'help_text')
        }),
        (_('قيود التحقق'), {
            'fields': ('min_length', 'max_length', 'min_value', 'max_value'),
            'classes': ('collapse',)
        }),
    )
