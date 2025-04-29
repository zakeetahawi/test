from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Branch, Department, Notification, CompanyInfo, FormField, SystemDBImportPermission, Salesperson
from django.urls import path
import os
import shutil
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseRedirect
import io

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
    list_display = ('name', 'code', 'department_type', 'parent', 'manager', 'is_active', 'order')
    list_filter = ('department_type', 'is_active', 'parent')
    search_fields = ('name', 'code', 'description')
    ordering = ['department_type', 'order', 'name']
    prepopulated_fields = {'code': ('name',)}
    raw_id_fields = ('parent', 'manager')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent', 'manager')

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'phone', 'email')
    ordering = ['code']

@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee_number', 'branch', 'phone', 'is_active']
    list_filter = ['branch', 'is_active']
    search_fields = ['name', 'employee_number', 'phone', 'email']
    ordering = ['name']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(branch=request.user.branch)
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "branch" and not request.user.is_superuser:
            kwargs["queryset"] = Branch.objects.filter(id=request.user.branch.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

from .forms import SystemDBImportPermissionForm

@admin.register(SystemDBImportPermission)
class SystemDBImportPermissionAdmin(admin.ModelAdmin):
    form = SystemDBImportPermissionForm
    filter_horizontal = ('users',)
    list_display = ('get_users', 'description')
    readonly_fields = ('db_import_export_link',)

    def has_add_permission(self, request):
        # إذا كان هناك صلاحية واحدة بالفعل، لا تظهر زر الإضافة
        if SystemDBImportPermission.objects.exists():
            return False
        return super().has_add_permission(request)

    def db_import_export_link(self, obj):
        from django.utils.safestring import mark_safe
        return mark_safe(f'<a class="button" href="/admin/accounts/systemdbimportpermission/db-import-export/" style="font-weight:bold; color:#fff; background:#007bff; padding:8px 18px; border-radius:5px; text-decoration:none;">الانتقال لصفحة استيراد/تصدير قاعدة البيانات</a>')
    db_import_export_link.short_description = 'استيراد/تصدير قاعدة البيانات'

    def get_users(self, obj):
        return ', '.join([user.username for user in obj.users.all()])
    get_users.short_description = 'المستخدمون'

    def save_model(self, request, obj, form, change):
        # تحقق من عدد المستخدمين قبل الحفظ
        users = form.cleaned_data.get('users')
        if users and users.count() > 2:
            messages.error(request, 'يسمح فقط باختيار مستخدمين اثنين كحد أقصى لاستيراد قاعدة البيانات!')
            return  # لا يتم الحفظ نهائيًا
        super().save_model(request, obj, form, change)

    # --- Custom Admin View for DB Import/Export ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('db-import-export/', self.admin_site.admin_view(self.db_import_export_view), name='db-import-export'),
        ]
        return custom_urls + urls

    import os, shutil
    from django.conf import settings
    def db_import_export_view(self, request):
        allowed_ids = SystemDBImportPermission.objects.first()
        if not allowed_ids or request.user not in allowed_ids.users.all():
            self.message_user(request, "ليس لديك صلاحية الوصول لهذه الصفحة!", level=messages.ERROR)
            return redirect('admin:index')
        context = dict(self.admin_site.each_context(request))
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        context['db_file_exists'] = os.path.exists(db_path)
        if request.method == 'POST':
            # تصدير ملف db.sqlite3 الأصلي
            if 'export_sqlite' in request.POST:
                if os.path.exists(db_path):
                    with open(db_path, 'rb') as dbfile:
                        response = HttpResponse(dbfile.read(), content_type='application/octet-stream')
                        response['Content-Disposition'] = 'attachment; filename=db.sqlite3'
                        return response
                else:
                    self.message_user(request, "ملف قاعدة البيانات غير موجود!", level=messages.ERROR)
            # استيراد ملف db.sqlite3 (استبدال الملف)
            elif 'import_sqlite' in request.FILES:
                sqlite_file = request.FILES['import_sqlite']
                if not sqlite_file.name.endswith('.sqlite3'):
                    self.message_user(request, "يجب رفع ملف بامتداد .sqlite3 فقط!", level=messages.ERROR)
                else:
                    try:
                        # عمل نسخة احتياطية قبل الاستبدال
                        if os.path.exists(db_path):
                            backup_path = db_path + '.bak'
                            shutil.copy2(db_path, backup_path)
                        # استبدال الملف
                        with open(db_path, 'wb') as dest:
                            for chunk in sqlite_file.chunks():
                                dest.write(chunk)
                        self.message_user(request, "تم رفع واستبدال قاعدة البيانات بنجاح!", level=messages.SUCCESS)
                        return HttpResponseRedirect(request.path)
                    except Exception as e:
                        self.message_user(request, f"حدث خطأ أثناء رفع قاعدة البيانات: {e}", level=messages.ERROR)
        return render(request, "admin/db_import_export.html", context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}
        # أضف رابط واضح لصفحة الاستيراد/التصدير
        extra_context['db_import_export_url'] = f'../db-import-export/'
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

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
