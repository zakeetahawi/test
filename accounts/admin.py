from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django import forms
from django.urls import path
from django.utils.html import format_html
from .models import (
    User, CompanyInfo, Branch, Notification, Department, Salesperson,
    Role, UserRole
)

class DepartmentFilter(admin.SimpleListFilter):
    title = _('Department')
    parameter_name = 'department'
    
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            departments = Department.objects.filter(is_active=True)
        else:
            departments = request.user.departments.filter(is_active=True)
        
        return [(dept.id, dept.name) for dept in departments]
    
    def queryset(self, request, queryset):
        if self.value():
            if hasattr(queryset.model, 'departments'):
                return queryset.filter(departments__id=self.value())
            elif hasattr(queryset.model, 'department'):
                return queryset.filter(department__id=self.value())
            elif hasattr(queryset.model, 'user') and hasattr(queryset.model.user.field.related_model, 'departments'):
                return queryset.filter(user__departments__id=self.value())
        return queryset

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'branch', 'first_name', 'last_name', 'is_staff', 'is_inspection_technician')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'branch', 'is_inspection_technician')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('معلومات شخصية'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'branch', 'departments')}),
        (_('الصلاحيات'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_inspection_technician', 'groups', 'user_permissions'),
        }),
        (_('تواريخ مهمة'), {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'website')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'logo', 'address', 'phone', 'email', 'website', 'working_hours')
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
            'fields': ('primary_color', 'secondary_color', 'accent_color', 'copyright_text')
        }),
        (_('معلومات النظام - للعرض فقط'), {
            'fields': ('developer', 'version', 'release_date'),
            'classes': ('collapse',),
            'description': 'هذه المعلومات للعرض فقط ولا يمكن تعديلها إلا من قبل مطور النظام.'
        }),
    )
    
    readonly_fields = ('developer', 'version', 'release_date')
    
    def has_add_permission(self, request):
        # Check if there's already an instance
        return not CompanyInfo.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the company info
        return False

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'phone', 'email')
    ordering = ['code']

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
    list_display = ('name', 'code', 'department_type', 'is_active', 'parent', 'manager')
    list_filter = (DepartmentFilter, 'department_type', 'is_active', 'parent')
    search_fields = ('name', 'code', 'description')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter by departments that the user belongs to
        user_departments = request.user.departments.all()
        # Include departments and their child departments
        department_ids = set()
        for dept in user_departments:
            department_ids.add(dept.id)
            # Add children recursively
            children = Department.objects.filter(parent=dept)
            for child in children:
                department_ids.add(child.id)
        return qs.filter(id__in=department_ids)
        
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'code', 'department_type', 'description', 'is_active')
        }),
        (_('العلاقات'), {
            'fields': ('parent', 'manager')
        }),
        (_('خيارات إضافية'), {
            'fields': ('order', 'icon', 'url_name', 'has_pages'),
            'classes': ('collapse',),
        }),
    )
    autocomplete_fields = ['parent', 'manager']

@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee_number', 'branch', 'is_active')
    list_filter = (DepartmentFilter, 'is_active', 'branch')
    search_fields = ('name', 'employee_number', 'phone', 'email')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'employee_number', 'branch', 'is_active')
        }),
        (_('معلومات الاتصال'), {
            'fields': ('phone', 'email', 'address')
        }),
        (_('معلومات إضافية'), {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter by branches that the user belongs to
        if request.user.branch:
            return qs.filter(branch=request.user.branch)
        return qs.none()

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_system_role', 'created_at', 'get_users_count')
    list_filter = ('is_system_role', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('معلومات الدور'), {
            'fields': ('name', 'description', 'is_system_role')
        }),
        (_('الصلاحيات'), {
            'fields': ('permissions',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_system_role=False)  # المستخدم العادي لا يمكنه رؤية أدوار النظام
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system_role:
            return False  # لا يمكن حذف أدوار النظام
        return super().has_delete_permission(request, obj)
    
    def get_users_count(self, obj):
        return obj.user_roles.count()
    get_users_count.short_description = _('عدد المستخدمين')

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'role__name')
    readonly_fields = ('assigned_at',)
    
    autocomplete_fields = ['user', 'role']
    
    fieldsets = (
        (_('معلومات العلاقة'), {
            'fields': ('user', 'role')
        }),
        (_('معلومات النظام'), {
            'fields': ('assigned_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'content_type')
    list_filter = ('content_type__app_label',)
    search_fields = ('name', 'codename')
    readonly_fields = ('codename', 'content_type')
    
    fieldsets = (
        (_('معلومات الصلاحية'), {
            'fields': ('name', 'codename', 'content_type')
        }),
    )
    
    def has_add_permission(self, request):
        return False  # لا يمكن إضافة صلاحيات جديدة من خلال واجهة الإدارة
    
    def has_delete_permission(self, request, obj=None):
        return False  # لا يمكن حذف صلاحيات من خلال واجهة الإدارة
