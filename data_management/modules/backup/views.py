"""
وجهات نظر وحدة النسخ الاحتياطي
"""

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator

from .models import BackupHistory, GoogleSheetsConfig, SyncLog
from .services import BackupService, GoogleSheetsService

def is_staff_or_superuser(user):
    """التحقق من أن المستخدم موظف أو مدير"""
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_superuser)
def dashboard(request):
    """عرض لوحة التحكم الرئيسية"""
    # إحصائيات النسخ الاحتياطي
    backup_service = BackupService()
    backup_stats = backup_service.get_backup_statistics()

    # آخر النسخ الاحتياطية
    recent_backups = BackupHistory.objects.order_by('-timestamp')[:10]

    # إعدادات Google Sheets
    google_sheets_config = GoogleSheetsConfig.objects.filter(is_active=True).first()

    # آخر عمليات المزامنة
    recent_syncs = SyncLog.objects.order_by('-timestamp')[:10]

    context = {
        'backup_stats': backup_stats,
        'recent_backups': recent_backups,
        'google_sheets_config': google_sheets_config,
        'recent_syncs': recent_syncs,
        'title': _('النسخ الاحتياطي ومزامنة البيانات'),
    }

    return render(request, 'data_management/backup/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def create_backup(request):
    """إنشاء نسخة احتياطية جديدة"""
    if request.method == 'POST':
        backup_type = request.POST.get('backup_type', 'full')
        is_compressed = request.POST.get('is_compressed', 'on') == 'on'
        is_encrypted = request.POST.get('is_encrypted', 'off') == 'on'

        try:
            # إنشاء النسخة الاحتياطية
            backup_service = BackupService()
            backup = backup_service.create_backup(
                backup_type=backup_type,
                is_compressed=is_compressed,
                is_encrypted=is_encrypted,
                created_by=request.user
            )

            messages.success(request, _('تم إنشاء النسخة الاحتياطية بنجاح.'))
            return redirect('data_management:backup_detail', pk=backup.pk)
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}'))
            return redirect('data_management:backup_dashboard')

    context = {
        'title': _('إنشاء نسخة احتياطية جديدة'),
    }

    return render(request, 'data_management/backup/create_backup.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def backup_list(request):
    """عرض قائمة النسخ الاحتياطية"""
    backups = BackupHistory.objects.all().order_by('-timestamp')

    # تصفية النتائج
    backup_type = request.GET.get('backup_type')
    status = request.GET.get('status')

    if backup_type:
        backups = backups.filter(backup_type=backup_type)

    if status:
        backups = backups.filter(status=status)

    # ترقيم الصفحات
    paginator = Paginator(backups, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'backup_type': backup_type,
        'status': status,
        'title': _('قائمة النسخ الاحتياطية'),
    }

    return render(request, 'data_management/backup/backup_list.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def backup_detail(request, pk):
    """عرض تفاصيل النسخة الاحتياطية"""
    backup = get_object_or_404(BackupHistory, pk=pk)

    context = {
        'backup': backup,
        'title': _('تفاصيل النسخة الاحتياطية'),
    }

    return render(request, 'data_management/backup/backup_detail.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def backup_download(request, pk):
    """تنزيل النسخة الاحتياطية"""
    backup = get_object_or_404(BackupHistory, pk=pk)

    # التحقق من وجود الملف
    if not os.path.exists(backup.backup_location):
        messages.error(request, _('ملف النسخة الاحتياطية غير موجود.'))
        return redirect('data_management:backup_detail', pk=backup.pk)

    # تنزيل الملف
    with open(backup.backup_location, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{backup.file_name}"'
        return response

@login_required
@user_passes_test(is_staff_or_superuser)
def restore_backup(request, pk):
    """استعادة النسخة الاحتياطية"""
    backup = get_object_or_404(BackupHistory, pk=pk)

    if request.method == 'POST':
        try:
            # استعادة النسخة الاحتياطية
            backup_service = BackupService()
            backup_service.restore_backup(backup.id)

            messages.success(request, _('تم استعادة النسخة الاحتياطية بنجاح.'))
            return redirect('data_management:backup_list')
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء استعادة النسخة الاحتياطية: {str(e)}'))
            return redirect('data_management:backup_detail', pk=backup.pk)

    context = {
        'backup': backup,
        'title': _('استعادة النسخة الاحتياطية'),
    }

    return render(request, 'data_management/backup/restore_backup.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def delete_backup(request, pk):
    """حذف النسخة الاحتياطية"""
    backup = get_object_or_404(BackupHistory, pk=pk)

    if request.method == 'POST':
        try:
            # حذف ملف النسخة الاحتياطية
            if os.path.exists(backup.backup_location):
                os.remove(backup.backup_location)

            # حذف سجل النسخة الاحتياطية
            backup.delete()

            messages.success(request, _('تم حذف النسخة الاحتياطية بنجاح.'))
            return redirect('data_management:backup_list')
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء حذف النسخة الاحتياطية: {str(e)}'))
            return redirect('data_management:backup_detail', pk=backup.pk)

    context = {
        'backup': backup,
        'title': _('حذف النسخة الاحتياطية'),
    }

    return render(request, 'data_management/backup/delete_backup.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def google_sheets_config(request):
    """إعدادات Google Sheets"""
    config = GoogleSheetsConfig.objects.filter(is_active=True).first()

    if request.method == 'POST':
        # تحديث الإعدادات
        sheet_id = request.POST.get('sheet_id')
        credentials_file = request.FILES.get('credentials_file')

        if not sheet_id:
            messages.error(request, _('يرجى إدخال معرف جدول البيانات.'))
            return redirect('data_management:google_sheets_config')

        if not config:
            # إنشاء إعدادات جديدة
            config = GoogleSheetsConfig(
                sheet_id=sheet_id,
                is_active=True
            )
        else:
            # تحديث الإعدادات الحالية
            config.sheet_id = sheet_id

        # تحديث ملف بيانات الاعتماد إذا تم تحميله
        if credentials_file:
            config.credentials_file = credentials_file

        # تحديث إعدادات المزامنة
        config.sync_customers = request.POST.get('sync_customers', 'off') == 'on'
        config.sync_products = request.POST.get('sync_products', 'off') == 'on'
        config.sync_orders = request.POST.get('sync_orders', 'off') == 'on'
        config.sync_inventory = request.POST.get('sync_inventory', 'off') == 'on'
        config.sync_inspections = request.POST.get('sync_inspections', 'off') == 'on'
        config.sync_installations = request.POST.get('sync_installations', 'off') == 'on'
        config.sync_company_info = request.POST.get('sync_company_info', 'off') == 'on'

        # تحديث جدولة المزامنة
        config.auto_sync = request.POST.get('auto_sync', 'off') == 'on'

        try:
            config.sync_interval = int(request.POST.get('sync_interval', 60))
        except ValueError:
            config.sync_interval = 60

        config.save()

        messages.success(request, _('تم حفظ إعدادات Google Sheets بنجاح.'))
        return redirect('data_management:google_sheets_config')

    context = {
        'config': config,
        'title': _('إعدادات Google Sheets'),
    }

    return render(request, 'data_management/backup/google_sheets_config.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def sync_google_sheets(request):
    """مزامنة Google Sheets"""
    config = GoogleSheetsConfig.objects.filter(is_active=True).first()

    if not config:
        messages.error(request, _('لا توجد إعدادات نشطة لمزامنة Google Sheets.'))
        return redirect('data_management:google_sheets_config')

    try:
        # مزامنة البيانات
        sync_service = GoogleSheetsService(config.id)
        sync_log = sync_service.sync_data()

        if sync_log.status == 'success':
            messages.success(request, _(f'تمت مزامنة {sync_log.records_synced} سجل بنجاح.'))
        elif sync_log.status == 'partial':
            messages.warning(request, _(f'تمت مزامنة {sync_log.records_synced} سجل بنجاح، ولكن حدثت بعض الأخطاء: {sync_log.errors}'))
        else:
            messages.error(request, _(f'فشلت المزامنة: {sync_log.errors}'))

        return redirect('data_management:sync_logs')
    except Exception as e:
        messages.error(request, _(f'حدث خطأ أثناء المزامنة: {str(e)}'))
        return redirect('data_management:google_sheets_config')

@login_required
@user_passes_test(is_staff_or_superuser)
def sync_logs(request):
    """عرض سجلات المزامنة"""
    logs = SyncLog.objects.all().order_by('-timestamp')

    # تصفية النتائج
    status = request.GET.get('status')

    if status:
        logs = logs.filter(status=status)

    # ترقيم الصفحات
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status': status,
        'title': _('سجلات المزامنة'),
    }

    return render(request, 'data_management/backup/sync_logs.html', context)
