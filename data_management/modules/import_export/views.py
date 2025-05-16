"""
وجهات نظر وحدة استيراد وتصدير البيانات
"""

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator
from django.apps import apps
from django.core.files import File

from .models import ImportExportLog, ImportTemplate
from .utils import process_import_file, generate_export_file, generate_template, get_model_from_string

def is_staff_or_superuser(user):
    """التحقق من أن المستخدم موظف أو مدير"""
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_superuser)
def dashboard(request):
    """عرض لوحة التحكم الرئيسية"""
    # إحصائيات الاستيراد/التصدير
    import_count = ImportExportLog.objects.filter(operation_type='import').count()
    export_count = ImportExportLog.objects.filter(operation_type='export').count()
    success_count = ImportExportLog.objects.filter(status='completed').count()
    failed_count = ImportExportLog.objects.filter(status='failed').count()

    # آخر العمليات
    recent_operations = ImportExportLog.objects.order_by('-created_at')[:10]

    # قوالب الاستيراد
    templates = ImportTemplate.objects.filter(is_active=True)

    context = {
        'import_count': import_count,
        'export_count': export_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'recent_operations': recent_operations,
        'templates': templates,
        'title': _('استيراد وتصدير البيانات'),
    }

    return render(request, 'data_management/import_export/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def import_data(request):
    """استيراد البيانات من ملف"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        model_name = request.POST.get('model_name')

        if not file:
            messages.error(request, _('يرجى اختيار ملف للاستيراد.'))
            return redirect('data_management:import_data')

        if not model_name:
            messages.error(request, _('يرجى اختيار نموذج للاستيراد.'))
            return redirect('data_management:import_data')

        # إنشاء سجل للعملية
        log = ImportExportLog.objects.create(
            operation_type='import',
            file_name=file.name,
            file=file,
            model_name=model_name,
            status='pending',
            created_by=request.user
        )

        try:
            # معالجة الملف
            result = process_import_file(file, model_name)

            # تحديث السجل
            log.records_count = result['total']
            log.success_count = result['success']
            log.error_count = result['errors']
            log.error_details = result['error_details']
            log.status = 'completed' if result['success'] > 0 else 'failed'
            log.completed_at = timezone.now()
            log.save()

            if result['success'] > 0:
                messages.success(request, _(f'تم استيراد {result["success"]} من {result["total"]} سجل بنجاح.'))
            else:
                messages.error(request, _('فشل استيراد البيانات. يرجى التحقق من تنسيق الملف.'))

            return redirect('data_management:log_detail', pk=log.pk)
        except Exception as e:
            # تحديث السجل في حالة الخطأ
            log.status = 'failed'
            log.error_details = str(e)
            log.completed_at = timezone.now()
            log.save()

            messages.error(request, _(f'حدث خطأ أثناء استيراد البيانات: {str(e)}'))
            return redirect('data_management:log_detail', pk=log.pk)

    # الحصول على قائمة النماذج المتاحة للاستيراد
    available_models = []
    for app_config in apps.get_app_configs():
        if app_config.name not in ['django', 'admin', 'contenttypes', 'sessions', 'messages', 'staticfiles']:
            for model in app_config.get_models():
                available_models.append((f"{app_config.name}.{model.__name__}", model._meta.verbose_name))

    # الحصول على قوالب الاستيراد
    templates = ImportTemplate.objects.filter(is_active=True)

    context = {
        'available_models': sorted(available_models, key=lambda x: x[1]),
        'templates': templates,
        'title': _('استيراد البيانات'),
    }

    return render(request, 'data_management/import_export/import.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def export_data(request):
    """تصدير البيانات إلى ملف"""
    if request.method == 'POST':
        model_name = request.POST.get('model_name')
        file_format = request.POST.get('file_format', 'xlsx')

        if not model_name:
            messages.error(request, _('يرجى اختيار نموذج للتصدير.'))
            return redirect('data_management:export_data')

        try:
            # الحصول على النموذج
            model = get_model_from_string(model_name)

            # الحصول على البيانات
            queryset = model.objects.all()

            # إنشاء سجل للعملية
            log = ImportExportLog.objects.create(
                operation_type='export',
                file_name=f"{model_name.replace('.', '_')}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{file_format}",
                model_name=model_name,
                status='processing',
                created_by=request.user
            )

            try:
                # إنشاء ملف التصدير
                temp_file_path = generate_export_file(queryset, file_format)

                # حفظ الملف في سجل العملية
                with open(temp_file_path, 'rb') as f:
                    log.file.save(log.file_name, File(f))

                # تحديث السجل
                log.records_count = queryset.count()
                log.success_count = queryset.count()
                log.status = 'completed'
                log.completed_at = timezone.now()
                log.save()

                # حذف الملف المؤقت
                os.remove(temp_file_path)

                messages.success(request, _(f'تم تصدير {queryset.count()} سجل بنجاح.'))

                # تنزيل الملف
                response = HttpResponse(log.file, content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{log.file_name}"'
                return response
            except Exception as e:
                # تحديث السجل في حالة الخطأ
                log.status = 'failed'
                log.error_details = str(e)
                log.completed_at = timezone.now()
                log.save()

                messages.error(request, _(f'حدث خطأ أثناء تصدير البيانات: {str(e)}'))
                return redirect('data_management:export_data')
        except Exception as e:
            messages.error(request, _(f'حدث خطأ: {str(e)}'))
            return redirect('data_management:export_data')

    # الحصول على قائمة النماذج المتاحة للتصدير
    available_models = []
    for app_config in apps.get_app_configs():
        if app_config.name not in ['django', 'admin', 'contenttypes', 'sessions', 'messages', 'staticfiles']:
            for model in app_config.get_models():
                available_models.append((f"{app_config.name}.{model.__name__}", model._meta.verbose_name))

    context = {
        'available_models': sorted(available_models, key=lambda x: x[1]),
        'title': _('تصدير البيانات'),
    }

    return render(request, 'data_management/import_export/export.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def log_list(request):
    """عرض قائمة سجلات الاستيراد/التصدير"""
    logs = ImportExportLog.objects.all().order_by('-created_at')

    # تصفية النتائج
    operation_type = request.GET.get('operation_type')
    status = request.GET.get('status')
    model_name = request.GET.get('model_name')

    if operation_type:
        logs = logs.filter(operation_type=operation_type)

    if status:
        logs = logs.filter(status=status)

    if model_name:
        logs = logs.filter(model_name=model_name)

    # ترقيم الصفحات
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'operation_type': operation_type,
        'status': status,
        'model_name': model_name,
        'title': _('سجلات الاستيراد/التصدير'),
    }

    return render(request, 'data_management/import_export/log_list.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def log_detail(request, pk):
    """عرض تفاصيل سجل الاستيراد/التصدير"""
    log = get_object_or_404(ImportExportLog, pk=pk)

    context = {
        'log': log,
        'title': _('تفاصيل سجل الاستيراد/التصدير'),
    }

    return render(request, 'data_management/import_export/log_detail.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def template_list(request):
    """عرض قائمة قوالب الاستيراد"""
    templates = ImportTemplate.objects.all().order_by('name')

    context = {
        'templates': templates,
        'title': _('قوالب الاستيراد'),
    }

    return render(request, 'data_management/import_export/template_list.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def template_detail(request, pk):
    """عرض تفاصيل قالب الاستيراد"""
    template = get_object_or_404(ImportTemplate, pk=pk)

    context = {
        'template': template,
        'title': _('تفاصيل قالب الاستيراد'),
    }

    return render(request, 'data_management/import_export/template_detail.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def template_download(request, pk):
    """تنزيل قالب الاستيراد"""
    template = get_object_or_404(ImportTemplate, pk=pk)

    response = HttpResponse(template.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{template.file.name.split("/")[-1]}"'
    return response
