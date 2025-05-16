"""
وجهات نظر تطبيق إدارة البيانات
"""

import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import connection

from data_management.modules.backup.models import BackupHistory
from data_management.modules.db_manager.models import DatabaseConfig

def is_staff_or_superuser(user):
    """التحقق من أن المستخدم موظف أو مدير"""
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_superuser)
def dashboard(request):
    """عرض لوحة التحكم الرئيسية"""
    # إحصائيات قاعدة البيانات
    database_config = settings.DATABASES['default']
    database_name = "crm_system"  # اسم قاعدة البيانات الافتراضي
    database_engine = "postgresql"  # نوع قاعدة البيانات الافتراضي
    database_user = "crm_user"  # اسم المستخدم الافتراضي
    database_password = "5525"  # كلمة المرور الافتراضية
    database_host = "localhost"  # المضيف الافتراضي
    database_port = "5432"  # المنفذ الافتراضي

    # جعل قاعدة البيانات الحالية قاعدة افتراضية
    try:
        # البحث عن قاعدة البيانات الحالية في النموذج
        db_config = DatabaseConfig.objects.filter(name=database_name).first()
        if not db_config:
            # إنشاء قاعدة بيانات جديدة إذا لم تكن موجودة
            db_config = DatabaseConfig.objects.create(
                name=database_name,
                db_type='postgresql',
                host=database_host,
                port=database_port,
                username=database_user,
                password=database_password,
                database_name=database_name,
                is_active=True,
                is_default=True
            )
        else:
            # تحديث قاعدة البيانات الحالية لتكون افتراضية
            db_config.is_default = True
            db_config.is_active = True
            db_config.save()
    except Exception as e:
        print(f"خطأ في إعداد قاعدة البيانات الافتراضية: {str(e)}")

    # حساب حجم قاعدة البيانات
    database_size = "غير متاح"
    if database_engine == 'postgresql':
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                database_size = cursor.fetchone()[0]
        except Exception as e:
            database_size = f"خطأ: {str(e)}"

    # إحصائيات النسخ الاحتياطي
    backup_count = BackupHistory.objects.count()
    last_backup = BackupHistory.objects.order_by('-timestamp').first()

    # إحصائيات غوغل درايف
    gdrive_backup_count = 0
    last_google_sync = None

    # إحصائيات الاستيراد والتصدير
    import_count = 0
    export_count = 0

    # قواعد البيانات المسجلة
    databases = DatabaseConfig.objects.all()

    # آخر النسخ الاحتياطية
    recent_backups = BackupHistory.objects.order_by('-timestamp')[:5]

    # آخر عمليات المزامنة
    recent_syncs = []

    context = {
        'database_name': database_name,
        'database_engine': database_engine,
        'database_size': database_size,
        'database_user': database_user,
        'database_password': database_password,
        'database_host': database_host,
        'database_port': database_port,
        'backup_count': backup_count,
        'last_backup': last_backup.timestamp if last_backup else _('لا توجد نسخ احتياطية'),
        'gdrive_backup_count': gdrive_backup_count,
        'last_google_sync': last_google_sync,
        'import_count': import_count,
        'export_count': export_count,
        'databases': databases,
        'recent_backups': recent_backups,
        'recent_syncs': recent_syncs,
        'title': _('إدارة البيانات'),
    }

    return render(request, 'data_management/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def google_sync_dashboard(request):
    """عرض لوحة تحكم مزامنة غوغل"""
    # إحصائيات غوغل شيتس
    last_sheets_sync = None
    sheets_records_count = 0
    sheets_auto_sync = False

    # إحصائيات غوغل درايف
    last_drive_backup = None
    drive_backup_count = 0
    drive_auto_backup = False

    # آخر عمليات المزامنة
    recent_syncs = []

    context = {
        'last_sheets_sync': last_sheets_sync,
        'sheets_records_count': sheets_records_count,
        'sheets_auto_sync': sheets_auto_sync,
        'last_drive_backup': last_drive_backup,
        'drive_backup_count': drive_backup_count,
        'drive_auto_backup': drive_auto_backup,
        'recent_syncs': recent_syncs,
        'title': _('مزامنة غوغل'),
    }

    return render(request, 'data_management/google_sync/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def google_sheets_config(request):
    """عرض وتحديث إعدادات غوغل شيتس"""
    if request.method == 'POST':
        # معالجة النموذج
        pass

    context = {
        'config': None,
        'title': _('إعدادات غوغل شيتس'),
    }

    return render(request, 'data_management/google_sync/google_sheets_config.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def google_sheets_sync(request):
    """مزامنة البيانات مع غوغل شيتس"""
    # تنفيذ المزامنة

    return redirect('data_management:google_sync')

@login_required
@user_passes_test(is_staff_or_superuser)
def gdrive_config(request):
    """عرض وتحديث إعدادات غوغل درايف"""
    if request.method == 'POST':
        # معالجة النموذج
        pass

    context = {
        'config': None,
        'title': _('إعدادات غوغل درايف'),
    }

    return render(request, 'data_management/google_sync/gdrive_config.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def backup_to_gdrive(request):
    """نسخ احتياطي لقاعدة البيانات على غوغل درايف"""
    # تنفيذ النسخ الاحتياطي

    return redirect('data_management:google_sync')

@login_required
@user_passes_test(is_staff_or_superuser)
def gdrive_backups(request):
    """عرض النسخ الاحتياطية على غوغل درايف"""
    context = {
        'backups': [],
        'title': _('النسخ الاحتياطية على غوغل درايف'),
    }

    return render(request, 'data_management/google_sync/gdrive_backups.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def schedule_sync(request):
    """جدولة المزامنة"""
    if request.method == 'POST':
        # معالجة النموذج
        pass

    context = {
        'sheets_config': None,
        'drive_config': None,
        'title': _('جدولة المزامنة'),
    }

    return render(request, 'data_management/google_sync/schedule_sync.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def sync_logs(request):
    """عرض سجلات المزامنة"""
    context = {
        'logs': [],
        'title': _('سجلات المزامنة'),
    }

    return render(request, 'data_management/google_sync/sync_logs.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def sync_log_detail(request, pk):
    """عرض تفاصيل سجل المزامنة"""
    context = {
        'log': None,
        'title': _('تفاصيل سجل المزامنة'),
    }

    return render(request, 'data_management/google_sync/sync_log_detail.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def excel_dashboard(request):
    """عرض لوحة تحكم استيراد وتصدير إكسل"""
    context = {
        'import_count': 0,
        'export_count': 0,
        'last_import': None,
        'last_export': None,
        'imported_records_count': 0,
        'exported_records_count': 0,
        'recent_imports': [],
        'recent_exports': [],
        'title': _('استيراد وتصدير إكسل'),
    }

    return render(request, 'data_management/excel/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def excel_import(request):
    """استيراد بيانات من ملف إكسل"""
    if request.method == 'POST':
        # معالجة النموذج
        pass

    context = {
        'title': _('استيراد من إكسل'),
    }

    return render(request, 'data_management/excel/import.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def excel_export(request):
    """تصدير بيانات إلى ملف إكسل"""
    if request.method == 'POST':
        # معالجة النموذج
        pass

    context = {
        'title': _('تصدير إلى إكسل'),
    }

    return render(request, 'data_management/excel/export.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def excel_template(request):
    """تنزيل قالب إكسل"""
    # إنشاء وتنزيل القالب

    return HttpResponse("Not implemented yet")

@login_required
@user_passes_test(is_staff_or_superuser)
def excel_import_logs(request):
    """عرض سجلات الاستيراد"""
    context = {
        'logs': [],
        'title': _('سجلات الاستيراد'),
    }

    return render(request, 'data_management/excel/import_logs.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def excel_export_logs(request):
    """عرض سجلات التصدير"""
    context = {
        'logs': [],
        'title': _('سجلات التصدير'),
    }

    return render(request, 'data_management/excel/export_logs.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def schedule_backup(request):
    """جدولة النسخ الاحتياطي"""
    if request.method == 'POST':
        # معالجة النموذج
        pass

    context = {
        'config': None,
        'title': _('جدولة النسخ الاحتياطي'),
    }

    return render(request, 'data_management/backup/schedule_backup.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def create_backup(request):
    """إنشاء نسخة احتياطية جديدة"""
    if request.method == 'POST':
        # معالجة النموذج
        pass

    # إعادة توجيه إلى صفحة النسخ الاحتياطي
    return redirect('data_management:backup_dashboard')

@login_required
@user_passes_test(is_staff_or_superuser)
def backup_list(request):
    """عرض قائمة النسخ الاحتياطية"""
    backups = BackupHistory.objects.all().order_by('-timestamp')

    context = {
        'backups': backups,
        'title': _('قائمة النسخ الاحتياطية'),
    }

    return render(request, 'data_management/backup/backup_list.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def db_export(request):
    """تصدير قاعدة البيانات"""
    if request.method == 'POST':
        # معالجة النموذج
        pass

    context = {
        'title': _('تصدير قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/export.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def db_import(request):
    """استيراد قاعدة البيانات"""
    if request.method == 'POST':
        # معالجة النموذج
        pass

    context = {
        'title': _('استيراد قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/import.html', context)
