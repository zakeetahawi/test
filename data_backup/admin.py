from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import os
import io
import hashlib
import tempfile
import subprocess
import json
from django.core.files import File
from wsgiref.util import FileWrapper
from .models import BackupHistory, GoogleSheetsConfig, SyncLog, SystemConfiguration, AutoBackupConfig, BackupNotificationSetting

@admin.register(BackupHistory)
class BackupHistoryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'backup_type', 'status', 'file_name', 'get_file_size_display', 'created_by')
    list_filter = ('backup_type', 'status', 'is_compressed', 'is_encrypted', 'timestamp')
    search_fields = ('file_name', 'error_message')
    readonly_fields = ('timestamp', 'file_checksum', 'file_size', 'created_by')
    
    fieldsets = (
        (_('معلومات النسخ الاحتياطي'), {
            'fields': ('backup_type', 'file_name', 'backup_location', 'file_size', 'file_checksum')
        }),
        (_('الخيارات'), {
            'fields': ('is_compressed', 'is_encrypted')
        }),
        (_('الحالة'), {
            'fields': ('status', 'error_message')
        }),
        (_('البيانات الوصفية'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'timestamp'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # عند إنشاء سجل جديد
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # السماح بحذف سجلات النسخ الاحتياطي
        if request.user.is_superuser:
            return True
        return False

    def delete_model(self, request, obj):
        """حذف الملف الفعلي عند حذف السجل"""
        try:
            # حذف الملف من المجلد إذا كان موجوداً
            if obj.backup_location and os.path.exists(obj.backup_location):
                os.remove(obj.backup_location)
        except Exception as e:
            self.message_user(request, f"تم حذف السجل ولكن فشل حذف الملف: {str(e)}", messages.WARNING)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """حذف الملفات الفعلية عند حذف مجموعة من السجلات"""
        for obj in queryset:
            try:
                if obj.backup_location and os.path.exists(obj.backup_location):
                    os.remove(obj.backup_location)
            except Exception as e:
                self.message_user(request, f"فشل حذف الملف {obj.file_name}: {str(e)}", messages.WARNING)
        super().delete_queryset(request, queryset)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create_backup/', self.admin_site.admin_view(self.create_backup), name='create_backup'),
            path('restore_backup/', self.admin_site.admin_view(self.restore_backup), name='restore_backup'),
            path('restore_status/', self.admin_site.admin_view(self.restore_status), name='restore_status'),
        ]
        return custom_urls + urls

    def create_backup(self, request):
        """إنشاء نسخة احتياطية من قاعدة البيانات وتحميلها مباشرة"""
        try:
            # التأكد من وجود مجلد النسخ المؤقتة
            tmp_dir = settings.DBBACKUP_TMP_DIR
            os.makedirs(tmp_dir, exist_ok=True)
            
            # إنشاء ملف مؤقت في المجلد المحدد
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_{timestamp}.psql'
            temp_path = os.path.join(tmp_dir, filename)
            
            # إنشاء النسخة الاحتياطية في الملف المؤقت
            call_command('dbbackup', '--output-filename', temp_path)
            
            # حساب حجم الملف والـ checksum
            with open(temp_path, 'rb') as f:
                file_content = f.read()
                file_size = len(file_content)
                checksum = hashlib.sha256(file_content).hexdigest()
            
            # تسجيل العملية في قاعدة البيانات
            backup = BackupHistory.objects.create(
                backup_type='manual',
                file_name=filename,
                file_size=file_size,
                status='success',
                file_checksum=checksum,
                backup_location=temp_path,
                created_by=request.user,
                metadata={
                    'created_at': timezone.now().isoformat(),
                    'created_by': request.user.username,
                }
            )
            
            # إعداد استجابة التحميل
            response = HttpResponse(
                FileWrapper(open(temp_path, 'rb')),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = file_size
            
            # حذف الملف المؤقت بعد التحميل
            def delete_file():
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            
            response.close = delete_file
            
            messages.success(request, _('تم إنشاء النسخة الاحتياطية بنجاح وجاري تحميلها.'))
            return response
            
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}'))
            return HttpResponseRedirect("../")

    def restore_backup(self, request):
        """استعادة قاعدة البيانات من نسخة احتياطية"""
        if request.method == 'POST' and 'backup_file' in request.FILES:
            try:
                uploaded_file = request.FILES['backup_file']
                # حفظ الملف في المجلد المؤقت
                tmp_dir = settings.DBBACKUP_TMP_DIR
                os.makedirs(tmp_dir, exist_ok=True)
                temp_path = os.path.join(tmp_dir, uploaded_file.name)
                
                with open(temp_path, 'wb') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)

                try:
                    # تحضير معلومات قاعدة البيانات
                    db_settings = settings.DATABASES['default']
                    env = os.environ.copy()
                    env['PGPASSWORD'] = db_settings['PASSWORD']

                    # إنشاء أمر الاستعادة
                    restore_command = [
                        'pg_restore',
                        '--host=' + db_settings['HOST'],
                        '--port=' + str(db_settings['PORT']),
                        '--username=' + db_settings['USER'],
                        '--dbname=' + db_settings['NAME'],
                        '--clean',
                        '--no-owner',
                        '--no-privileges',
                        temp_path
                    ]

                    # تنفيذ عملية الاستعادة
                    process = subprocess.Popen(
                        restore_command,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    stdout, stderr = process.communicate()

                    if process.returncode != 0:
                        raise Exception(f'فشلت عملية الاستعادة: {stderr.decode()}')

                    # تسجيل نجاح العملية
                    BackupHistory.objects.create(
                        backup_type='manual',
                        file_name=os.path.basename(temp_path),
                        file_size=os.path.getsize(temp_path),
                        status='restored',
                        backup_location=temp_path,
                        created_by=request.user,
                        metadata={
                            'restored_at': timezone.now().isoformat(),
                            'restored_by': request.user.username,
                        }
                    )

                    messages.success(request, _('تمت استعادة قاعدة البيانات بنجاح.'))

                except Exception as e:
                    messages.error(request, _(f'فشلت عملية الاستعادة: {str(e)}'))

                finally:
                    # حذف الملف المؤقت
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

                return HttpResponseRedirect("../")

            except Exception as e:
                messages.error(request, _(f'حدث خطأ أثناء معالجة الملف: {str(e)}'))

        return render(request, 'admin/data_backup/backuphistory/restore_form.html')

    def restore_status(self, request):
        """إرجاع حالة عملية الاستعادة كاستجابة JSON"""
        process_id = request.session.get('restore_process_id')
        if not process_id:
            return JsonResponse({
                'status': 'error',
                'progress': 0,
                'message': 'لم يتم العثور على معرف العملية'
            })
            
        # جلب حالة العملية من الكاش
        status_data = cache.get(f"{process_id}_status")
        if not status_data:
            return JsonResponse({
                'status': 'error',
                'progress': 0,
                'message': 'انتهت صلاحية العملية'
            })
            
        return JsonResponse(status_data)

    def _perform_restore(self, file_path, user_id, process_id):
        """تنفيذ عملية الاستعادة"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        try:
            # التحقق من الملف - 10%
            cache.set(f"{process_id}_status", {
                'status': 'in_progress',
                'progress': 10,
                'message': 'جاري التحقق من صحة ملف النسخة الاحتياطية...'
            }, timeout=3600)
            
            if not os.path.exists(file_path):
                raise Exception('ملف النسخة الاحتياطية غير موجود')
            
            # استعادة قاعدة البيانات - 25%
            cache.set(f"{process_id}_status", {
                'status': 'in_progress',
                'progress': 25,
                'message': 'جاري تحضير قاعدة البيانات للاستعادة...'
            }, timeout=3600)
            
            # الحصول على معلومات اتصال قاعدة البيانات
            db_settings = settings.DATABASES['default']
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings['PASSWORD']
            
            # تنفيذ الاستعادة باستخدام pg_restore مباشرة - 50%
            cache.set(f"{process_id}_status", {
                'status': 'in_progress',
                'progress': 50,
                'message': 'جاري استعادة قاعدة البيانات...'
            }, timeout=3600)
            
            restore_command = [
                'pg_restore',
                '--host=' + db_settings['HOST'],
                '--port=' + db_settings['PORT'],
                '--username=' + db_settings['USER'],
                '--dbname=' + db_settings['NAME'],
                '--clean',
                '--no-owner',
                file_path
            ]
            
            process = subprocess.Popen(
                restore_command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f'فشلت عملية الاستعادة: {stderr.decode()}')
            
            # تحديث التقدم - 75%
            cache.set(f"{process_id}_status", {
                'status': 'in_progress',
                'progress': 75,
                'message': 'جاري إكمال عملية الاستعادة...'
            }, timeout=3600)
            
            # تسجيل العملية
            BackupHistory.objects.create(
                backup_type='manual',
                file_name=os.path.basename(file_path),
                file_size=os.path.getsize(file_path),
                status='restored',
                backup_location=file_path,
                created_by=user,
                metadata={
                    'restored_at': timezone.now().isoformat(),
                    'restored_by': user.username,
                }
            )
            
            # تحديث اكتمال العملية - 100%
            cache.set(f"{process_id}_status", {
                'status': 'completed',
                'progress': 100,
                'message': 'تمت استعادة قاعدة البيانات بنجاح'
            }, timeout=3600)
            
        except Exception as e:
            # تحديث حالة الفشل
            cache.set(f"{process_id}_status", {
                'status': 'failed',
                'progress': 0,
                'message': f'فشلت عملية الاستعادة: {str(e)}'
            }, timeout=3600)
        
        finally:
            # حذف الملف المؤقت
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass

    actions = ['create_backup_action']

    def create_backup_action(self, request, queryset):
        """إجراء إنشاء نسخة احتياطية من خلال قائمة الإجراءات"""
        return self.create_backup(request)
    create_backup_action.short_description = _('إنشاء نسخة احتياطية جديدة')

@admin.register(GoogleSheetsConfig)
class GoogleSheetsConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_active', 'auto_sync_enabled', 'last_sync')
    list_filter = ('is_active', 'auto_sync_enabled')
    fieldsets = (
        (_('الإعدادات الأساسية'), {
            'fields': ('spreadsheet_id', 'credentials_file', 'is_active')
        }),
        (_('إعدادات المزامنة التلقائية'), {
            'fields': ('auto_sync_enabled', 'sync_interval_minutes', 'last_sync')
        }),
        (_('الجداول المزامنة'), {
            'fields': (
                'sync_customers', 'sync_orders', 'sync_products',
                'sync_inspections', 'sync_installations'
            )
        }),
        (_('مزامنة البيانات النصية'), {
            'fields': (
                'sync_company_info', 'sync_contact_details', 'sync_system_settings'
            )
        }),
    )
    readonly_fields = ('last_sync',)

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'status', 'records_synced', 'triggered_by')
    list_filter = ('status', 'timestamp')
    search_fields = ('details',)
    readonly_fields = ('timestamp', 'triggered_by')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('category', 'key', 'updated_at')
    list_filter = ('category', 'updated_at')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('updated_at',)
    
    fieldsets = (
        (None, {
            'fields': ('category', 'key', 'value', 'description')
        }),
        (_('معلومات النظام'), {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(AutoBackupConfig)
class AutoBackupConfigAdmin(admin.ModelAdmin):
    list_display = ('enabled', 'interval', 'time', 'last_backup', 'next_backup')
    list_filter = ('enabled', 'interval', 'compression_enabled', 'encryption_enabled')
    
    fieldsets = (
        (_('الإعدادات الأساسية'), {
            'fields': ('enabled', 'interval', 'time')
        }),
        (_('إعدادات الحفظ'), {
            'fields': ('retention_days', 'compression_enabled')
        }),
        (_('إعدادات التشفير'), {
            'fields': ('encryption_enabled', 'encryption_key'),
            'classes': ('collapse',),
            'description': _('تنبيه: احفظ مفتاح التشفير في مكان آمن، لن تتمكن من استعادة النسخ الاحتياطية بدونه.')
        }),
        (_('معلومات الحالة'), {
            'fields': ('last_backup', 'next_backup'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('last_backup', 'next_backup')
    
    def save_model(self, request, obj, form, change):
        if obj.encryption_enabled and not obj.encryption_key:
            messages.error(request, _('يجب تحديد مفتاح التشفير عند تفعيل خاصية التشفير.'))
            return
        
        super().save_model(request, obj, form, change)

@admin.register(BackupNotificationSetting)
class BackupNotificationSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'notify_on_success', 'notify_on_failure', 'notify_on_restore', 'email_notifications')
    list_filter = ('notify_on_success', 'notify_on_failure', 'notify_on_restore', 'email_notifications')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return request.user.is_superuser or obj.user == request.user
    
    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        return request.user.is_superuser or obj.user == request.user
    
    def save_model(self, request, obj, form, change):
        if not change:  # عند إنشاء إعدادات جديدة
            obj.user = request.user
        super().save_model(request, obj, form, change)
