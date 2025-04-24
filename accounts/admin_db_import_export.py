from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseRedirect
from .models import SystemDBImportPermission
import io, os

User = get_user_model()

@admin.register(SystemDBImportPermission)
class SystemDBImportPermissionAdmin(admin.ModelAdmin):
    filter_horizontal = ('users',)
    list_display = ('get_users', 'description')
    def get_users(self, obj):
        return ', '.join([user.username for user in obj.users.all()])
    get_users.short_description = 'المستخدمون'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.users.count() > 2:
            from django.contrib import messages
            messages.error(request, 'يسمح فقط باختيار مستخدمين اثنين كحد أقصى لاستيراد قاعدة البيانات!')

# --- Custom Admin View for DB Import/Export ---
class DBImportExportAdminView(admin.ModelAdmin):
    change_list_template = "admin/db_import_export.html"
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('db-import-export/', self.admin_site.admin_view(self.db_import_export_view), name='db-import-export'),
        ]
        return custom_urls + urls

    def db_import_export_view(self, request):
        # Check permission: user must be in SystemDBImportPermission
        allowed_ids = SystemDBImportPermission.objects.first()
        if not allowed_ids or request.user not in allowed_ids.users.all():
            self.message_user(request, "ليس لديك صلاحية الوصول لهذه الصفحة!", level=messages.ERROR)
            return redirect('admin:index')
        context = dict(
            self.admin_site.each_context(request),
        )
        if request.method == 'POST' and 'import_file' in request.FILES:
            import_file = request.FILES['import_file']
            try:
                data = io.TextIOWrapper(import_file.file, encoding='utf-8')
                call_command('loaddata', data)
                self.message_user(request, "تم استيراد البيانات بنجاح.", level=messages.SUCCESS)
                return HttpResponseRedirect(request.path)
            except Exception as e:
                self.message_user(request, f"حدث خطأ أثناء الاستيراد: {e}", level=messages.ERROR)
        elif request.method == 'POST' and 'export' in request.POST:
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename=db_export.json'
            out = io.StringIO()
            call_command('dumpdata', stdout=out)
            response.write(out.getvalue())
            return response
        return render(request, "admin/db_import_export.html", context)
