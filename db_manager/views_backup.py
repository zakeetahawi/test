from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.db.utils import OperationalError
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.urls import reverse

from .models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken
from .forms import (
    DatabaseConfigForm, DatabaseBackupForm, DatabaseImportForm,
    SetupTokenForm, DatabaseSetupForm
)

import os
import json
import tempfile
import subprocess
from datetime import datetime, timedelta
import io
import psycopg2
import sqlite3
import uuid
import threading


@login_required
@user_passes_test(is_superuser)
def backup_list(request):
    """عرض قائمة النسخ الاحتياطية"""
    backups = DatabaseBackup.objects.all()
    return render(request, 'db_manager/backup_list.html', {
        'backups': backups,
    })


@login_required
@user_passes_test(is_superuser)
def backup_create(request):
    """إنشاء نسخة احتياطية جديدة"""
    if request.method == 'POST':
        form = DatabaseBackupForm(request.POST, user=request.user)
        if form.is_valid():
            backup = form.save(commit=False)
            
            # إنشاء النسخة الاحتياطية
            db_config = backup.database_config
            
            # إنشاء ملف مؤقت للنسخة الاحتياطية
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # استخدام أمر Django لتصدير البيانات
                if db_config.db_type == 'postgresql':
                    # تعيين متغيرات البيئة للاتصال بقاعدة البيانات
                    os.environ['PGHOST'] = db_config.host
                    os.environ['PGPORT'] = db_config.port or '5432'
                    os.environ['PGDATABASE'] = db_config.database_name
                    os.environ['PGUSER'] = db_config.username
                    os.environ['PGPASSWORD'] = db_config.password
                    
                    # تنفيذ أمر pg_dump
                    cmd = [
                        'pg_dump',
                        '--format=custom',
                        '--file=' + temp_path,
                        db_config.database_name
                    ]
                    subprocess.run(cmd, check=True)
                elif db_config.db_type == 'sqlite':
                    # استخدام أمر Django dumpdata
                    call_command(
                        'dumpdata',
                        '--exclude', 'auth.permission',
                        '--exclude', 'contenttypes',
                        '--indent', '2',
                        '--output', temp_path
                    )
                
                # حفظ الملف في حقل الملف
                with open(temp_path, 'rb') as f:
                    file_name = f"{backup.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    if db_config.db_type == 'postgresql':
                        file_name += '.dump'
                    else:
                        file_name += '.json'
                    
                    backup.file.save(file_name, ContentFile(f.read()))
                
                # حفظ النسخة الاحتياطية
                backup.save()
                
                messages.success(request, _('تم إنشاء النسخة الاحتياطية بنجاح.'))
                return redirect('db_manager:backup_list')
            except Exception as e:
                messages.error(request, _('حدث خطأ أثناء إنشاء النسخة الاحتياطية: {}').format(str(e)))
            finally:
                # حذف الملف المؤقت
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
    else:
        form = DatabaseBackupForm(user=request.user)
    
    return render(request, 'db_manager/backup_form.html', {
        'form': form,
        'title': _('إنشاء نسخة احتياطية جديدة'),
    })


@login_required
@user_passes_test(is_superuser)
def backup_download(request, pk):
    """تنزيل ملف النسخة الاحتياطية"""
    backup = get_object_or_404(DatabaseBackup, pk=pk)
    
    # التحقق من وجود الملف
    if not backup.file:
        messages.error(request, _('ملف النسخة الاحتياطية غير موجود.'))
        return redirect('db_manager:backup_list')
    
    # إنشاء استجابة لتنزيل الملف
    response = HttpResponse(
        backup.file.read(),
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(backup.file.name)}"'
    
    return response


@login_required
@user_passes_test(is_superuser)
def backup_restore(request, pk):
    """استعادة النسخة الاحتياطية"""
    backup = get_object_or_404(DatabaseBackup, pk=pk)
    
    if request.method == 'POST':
        # التحقق من وجود الملف
        if not backup.file:
            messages.error(request, _('ملف النسخة الاحتياطية غير موجود.'))
            return redirect('db_manager:backup_list')
        
        # إنشاء سجل استيراد جديد
        db_import = DatabaseImport.objects.create(
            file=backup.file,
            database_config=backup.database_config,
            status='in_progress',
            created_by=request.user
        )
        
        # بدء عملية الاستيراد في خلفية منفصلة
        thread = threading.Thread(
            target=process_import,
            args=(db_import.id,)
        )
        thread.start()
        
        messages.success(request, _('بدأت عملية استعادة النسخة الاحتياطية. يمكنك متابعة التقدم في صفحة الاستيراد.'))
        return redirect('db_manager:import_status', pk=db_import.id)
    
    return render(request, 'db_manager/backup_confirm_restore.html', {
        'backup': backup,
    })


@login_required
@user_passes_test(is_superuser)
def backup_delete(request, pk):
    """حذف النسخة الاحتياطية"""
    backup = get_object_or_404(DatabaseBackup, pk=pk)
    
    if request.method == 'POST':
        # حذف الملف
        if backup.file:
            backup.file.delete()
        
        # حذف السجل
        backup.delete()
        
        messages.success(request, _('تم حذف النسخة الاحتياطية بنجاح.'))
        return redirect('db_manager:backup_list')
    
    return render(request, 'db_manager/backup_confirm_delete.html', {
        'backup': backup,
    })


@login_required
@user_passes_test(is_superuser)
def database_import(request):
    """استيراد قاعدة بيانات من ملف"""
    if request.method == 'POST':
        form = DatabaseImportForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            db_import = form.save()
            
            # بدء عملية الاستيراد في خلفية منفصلة
            thread = threading.Thread(
                target=process_import,
                args=(db_import.id,)
            )
            thread.start()
            
            messages.success(request, _('بدأت عملية الاستيراد. يمكنك متابعة التقدم في صفحة الحالة.'))
            return redirect('db_manager:import_status', pk=db_import.id)
    else:
        form = DatabaseImportForm(user=request.user)
    
    return render(request, 'db_manager/import_form.html', {
        'form': form,
    })


def process_import(import_id):
    """معالجة عملية استيراد قاعدة البيانات"""
    db_import = DatabaseImport.objects.get(id=import_id)
    
    try:
        # تحديث الحالة
        db_import.status = 'in_progress'
        db_import.save()
        
        # الحصول على مسار الملف
        file_path = db_import.file.path
        
        # تحديد نوع الملف
        is_json = file_path.lower().endswith('.json')
        is_dump = file_path.lower().endswith('.dump')
        
        # استيراد البيانات
        if is_json:
            # استخدام أمر Django loaddata
            output = io.StringIO()
            call_command(
                'loaddata',
                file_path,
                stdout=output
            )
            db_import.log = output.getvalue()
        elif is_dump:
            # استخدام أمر pg_restore
            db_config = db_import.database_config
            
            # تعيين متغيرات البيئة للاتصال بقاعدة البيانات
            os.environ['PGHOST'] = db_config.host
            os.environ['PGPORT'] = db_config.port or '5432'
            os.environ['PGDATABASE'] = db_config.database_name
            os.environ['PGUSER'] = db_config.username
            os.environ['PGPASSWORD'] = db_config.password
            
            # تنفيذ أمر pg_restore
            cmd = [
                'pg_restore',
                '--dbname=' + db_config.database_name,
                '--clean',
                '--if-exists',
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            db_import.log = result.stdout + '\n' + result.stderr
        
        # تحديث الحالة
        db_import.status = 'completed'
        db_import.completed_at = timezone.now()
        db_import.save()
    except Exception as e:
        # تحديث الحالة في حالة الفشل
        db_import.status = 'failed'
        db_import.log = str(e)
        db_import.save()


@login_required
@user_passes_test(is_superuser)
def database_export(request):
    """تصدير قاعدة البيانات إلى ملف"""
    if request.method == 'POST':
        db_config_id = request.POST.get('database_config')
        export_format = request.POST.get('format', 'json')
        
        if not db_config_id:
            messages.error(request, _('يرجى اختيار قاعدة بيانات.'))
            return redirect('db_manager:database_list')
        
        db_config = get_object_or_404(DatabaseConfig, pk=db_config_id)
        
        # إنشاء ملف مؤقت للتصدير
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # تصدير البيانات
            if export_format == 'json':
                # استخدام أمر Django dumpdata
                call_command(
                    'dumpdata',
                    '--exclude', 'auth.permission',
                    '--exclude', 'contenttypes',
                    '--indent', '2',
                    '--output', temp_path
                )
                
                # إنشاء استجابة لتنزيل الملف
                with open(temp_path, 'rb') as f:
                    response = HttpResponse(
                        f.read(),
                        content_type='application/json'
                    )
                    response['Content-Disposition'] = f'attachment; filename="db_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            elif export_format == 'dump' and db_config.db_type == 'postgresql':
                # تعيين متغيرات البيئة للاتصال بقاعدة البيانات
                os.environ['PGHOST'] = db_config.host
                os.environ['PGPORT'] = db_config.port or '5432'
                os.environ['PGDATABASE'] = db_config.database_name
                os.environ['PGUSER'] = db_config.username
                os.environ['PGPASSWORD'] = db_config.password
                
                # تنفيذ أمر pg_dump
                cmd = [
                    'pg_dump',
                    '--format=custom',
                    '--file=' + temp_path,
                    db_config.database_name
                ]
                subprocess.run(cmd, check=True)
                
                # إنشاء استجابة لتنزيل الملف
                with open(temp_path, 'rb') as f:
                    response = HttpResponse(
                        f.read(),
                        content_type='application/octet-stream'
                    )
                    response['Content-Disposition'] = f'attachment; filename="db_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.dump"'
            else:
                messages.error(request, _('تنسيق التصدير غير مدعوم.'))
                return redirect('db_manager:database_list')
            
            # حذف الملف المؤقت
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            return response
        except Exception as e:
            messages.error(request, _('حدث خطأ أثناء تصدير قاعدة البيانات: {}').format(str(e)))
            
            # حذف الملف المؤقت في حالة الفشل
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            return redirect('db_manager:database_list')
    
    # عرض نموذج التصدير
    databases = DatabaseConfig.objects.filter(is_active=True)
    
    return render(request, 'db_manager/export_form.html', {
        'databases': databases,
    })


@login_required
@user_passes_test(is_superuser)
def import_status(request, pk):
    """عرض حالة عملية الاستيراد"""
    db_import = get_object_or_404(DatabaseImport, pk=pk)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # استجابة AJAX لتحديث الحالة
        return JsonResponse({
            'status': db_import.status,
            'completed_at': db_import.completed_at.isoformat() if db_import.completed_at else None,
            'log': db_import.log,
        })
    
    return render(request, 'db_manager/import_status.html', {
        'db_import': db_import,
    })


@login_required
@user_passes_test(is_superuser)
def token_list(request):
    """عرض قائمة رموز الإعداد"""
    tokens = SetupToken.objects.all()
    return render(request, 'db_manager/token_list.html', {
        'tokens': tokens,
    })


@login_required
@user_passes_test(is_superuser)
def token_create(request):
    """إنشاء رمز إعداد جديد"""
    if request.method == 'POST':
        form = SetupTokenForm(request.POST)
        if form.is_valid():
            token = form.save()
            
            setup_url = request.build_absolute_uri(
                reverse('db_manager:setup_with_token', args=[token.token])
            )
            
            messages.success(request, _('تم إنشاء رمز الإعداد بنجاح.'))
            return render(request, 'db_manager/token_created.html', {
                'token': token,
                'setup_url': setup_url,
            })
    else:
        form = SetupTokenForm()
    
    return render(request, 'db_manager/token_form.html', {
        'form': form,
    })


@login_required
@user_passes_test(is_superuser)
def token_delete(request, pk):
    """حذف رمز إعداد"""
    token = get_object_or_404(SetupToken, pk=pk)
    
    if request.method == 'POST':
        token.delete()
        messages.success(request, _('تم حذف رمز الإعداد بنجاح.'))
        return redirect('db_manager:token_list')
    
    return render(request, 'db_manager/token_confirm_delete.html', {
        'token': token,
    })
