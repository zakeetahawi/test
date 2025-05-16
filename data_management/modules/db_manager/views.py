"""
وجهات نظر وحدة إدارة قواعد البيانات
"""

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken
from .forms import DatabaseConfigForm, DatabaseBackupForm, DatabaseImportForm, SetupTokenForm, DatabaseSetupForm
from .services import DatabaseService

def is_superuser(user):
    """التحقق من أن المستخدم مدير"""
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def dashboard(request):
    """عرض لوحة التحكم الرئيسية"""
    # إحصائيات قواعد البيانات
    database_count = DatabaseConfig.objects.count()
    active_database = DatabaseConfig.objects.filter(is_active=True).first()
    default_database = DatabaseConfig.objects.filter(is_default=True).first()

    # إحصائيات النسخ الاحتياطي
    backup_count = DatabaseBackup.objects.count()
    recent_backups = DatabaseBackup.objects.order_by('-created_at')[:5]

    # إحصائيات الاستيراد
    import_count = DatabaseImport.objects.count()
    recent_imports = DatabaseImport.objects.order_by('-created_at')[:5]

    # رموز الإعداد
    setup_tokens = SetupToken.objects.filter(is_used=False, expires_at__gt=timezone.now())

    context = {
        'database_count': database_count,
        'active_database': active_database,
        'default_database': default_database,
        'backup_count': backup_count,
        'recent_backups': recent_backups,
        'import_count': import_count,
        'recent_imports': recent_imports,
        'setup_tokens': setup_tokens,
        'title': _('إدارة قواعد البيانات'),
    }

    return render(request, 'data_management/db_manager/dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def database_list(request):
    """عرض قائمة قواعد البيانات"""
    databases = DatabaseConfig.objects.all().order_by('-is_default', '-is_active', 'name')

    context = {
        'databases': databases,
        'title': _('قائمة قواعد البيانات'),
    }

    return render(request, 'data_management/db_manager/database_list.html', context)

@login_required
@user_passes_test(is_superuser)
def database_create(request):
    """إنشاء قاعدة بيانات جديدة"""
    if request.method == 'POST':
        form = DatabaseConfigForm(request.POST)
        if form.is_valid():
            database = form.save()
            messages.success(request, _('تم إنشاء قاعدة البيانات بنجاح.'))
            return redirect('data_management:database_detail', pk=database.pk)
    else:
        form = DatabaseConfigForm()

    context = {
        'form': form,
        'title': _('إنشاء قاعدة بيانات جديدة'),
    }

    return render(request, 'data_management/db_manager/database_form.html', context)

@login_required
@user_passes_test(is_superuser)
def database_detail(request, pk):
    """عرض تفاصيل قاعدة البيانات"""
    database = get_object_or_404(DatabaseConfig, pk=pk)

    # الحصول على النسخ الاحتياطية لقاعدة البيانات
    backups = DatabaseBackup.objects.filter(database_config=database).order_by('-created_at')

    # الحصول على عمليات الاستيراد لقاعدة البيانات
    imports = DatabaseImport.objects.filter(database_config=database).order_by('-created_at')

    context = {
        'database': database,
        'backups': backups,
        'imports': imports,
        'title': _('تفاصيل قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/database_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def database_update(request, pk):
    """تحديث قاعدة بيانات"""
    database = get_object_or_404(DatabaseConfig, pk=pk)

    if request.method == 'POST':
        form = DatabaseConfigForm(request.POST, instance=database)
        if form.is_valid():
            database = form.save()
            messages.success(request, _('تم تحديث قاعدة البيانات بنجاح.'))
            return redirect('data_management:database_detail', pk=database.pk)
    else:
        form = DatabaseConfigForm(instance=database)

    context = {
        'form': form,
        'database': database,
        'title': _('تحديث قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/database_form.html', context)

@login_required
@user_passes_test(is_superuser)
def database_delete(request, pk):
    """حذف قاعدة بيانات"""
    database = get_object_or_404(DatabaseConfig, pk=pk)

    if request.method == 'POST':
        database.delete()
        messages.success(request, _('تم حذف قاعدة البيانات بنجاح.'))
        return redirect('data_management:database_list')

    context = {
        'database': database,
        'title': _('حذف قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/database_delete.html', context)

@login_required
@user_passes_test(is_superuser)
def database_set_default(request, pk):
    """تعيين قاعدة البيانات كافتراضية"""
    database = get_object_or_404(DatabaseConfig, pk=pk)

    if request.method == 'POST':
        # تعيين قاعدة البيانات كافتراضية
        database.is_default = True
        database.save()

        messages.success(request, _('تم تعيين قاعدة البيانات كافتراضية بنجاح.'))
        return redirect('data_management:database_detail', pk=database.pk)

    context = {
        'database': database,
        'title': _('تعيين قاعدة البيانات كافتراضية'),
    }

    return render(request, 'data_management/db_manager/database_set_default.html', context)

@login_required
@user_passes_test(is_superuser)
def backup_list(request):
    """عرض قائمة النسخ الاحتياطية"""
    backups = DatabaseBackup.objects.all().order_by('-created_at')

    # تصفية النتائج
    database_id = request.GET.get('database_id')
    backup_type = request.GET.get('backup_type')

    if database_id:
        backups = backups.filter(database_config_id=database_id)

    if backup_type:
        backups = backups.filter(backup_type=backup_type)

    # ترقيم الصفحات
    paginator = Paginator(backups, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # الحصول على قائمة قواعد البيانات
    databases = DatabaseConfig.objects.all()

    context = {
        'page_obj': page_obj,
        'databases': databases,
        'database_id': database_id,
        'backup_type': backup_type,
        'title': _('قائمة النسخ الاحتياطية'),
    }

    return render(request, 'data_management/db_manager/backup_list.html', context)

@login_required
@user_passes_test(is_superuser)
def backup_create(request):
    """إنشاء نسخة احتياطية جديدة"""
    if request.method == 'POST':
        form = DatabaseBackupForm(request.POST)
        if form.is_valid():
            # الحصول على البيانات من النموذج
            database_config = form.cleaned_data['database_config']
            backup_type = form.cleaned_data['backup_type']
            description = form.cleaned_data['description']

            try:
                # إنشاء النسخة الاحتياطية
                database_service = DatabaseService(database_config.id)
                backup = database_service.create_backup(
                    database_config=database_config,
                    backup_type=backup_type,
                    description=description,
                    created_by=request.user
                )

                messages.success(request, _('تم إنشاء النسخة الاحتياطية بنجاح.'))
                return redirect('data_management:db_backup_detail', pk=backup.pk)
            except Exception as e:
                messages.error(request, _(f'حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}'))
                return redirect('data_management:db_backup_create')
    else:
        form = DatabaseBackupForm()

    context = {
        'form': form,
        'title': _('إنشاء نسخة احتياطية جديدة'),
    }

    return render(request, 'data_management/db_manager/backup_form.html', context)

@login_required
@user_passes_test(is_superuser)
def backup_detail(request, pk):
    """عرض تفاصيل النسخة الاحتياطية"""
    backup = get_object_or_404(DatabaseBackup, pk=pk)

    context = {
        'backup': backup,
        'title': _('تفاصيل النسخة الاحتياطية'),
    }

    return render(request, 'data_management/db_manager/backup_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def backup_download(request, pk):
    """تنزيل النسخة الاحتياطية"""
    backup = get_object_or_404(DatabaseBackup, pk=pk)

    # التحقق من وجود الملف
    file_path = os.path.join(settings.MEDIA_ROOT, backup.file.name)
    if not os.path.exists(file_path):
        messages.error(request, _('ملف النسخة الاحتياطية غير موجود.'))
        return redirect('data_management:db_backup_detail', pk=backup.pk)

    # تنزيل الملف
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(backup.file.name)}"'
        return response

@login_required
@user_passes_test(is_superuser)
def backup_restore(request, pk):
    """استعادة النسخة الاحتياطية"""
    backup = get_object_or_404(DatabaseBackup, pk=pk)

    if request.method == 'POST':
        # الحصول على خيار حذف البيانات القديمة
        clear_data = request.POST.get('clear_data', 'off') == 'on'

        try:
            # استعادة النسخة الاحتياطية
            database_service = DatabaseService(backup.database_config.id)
            database_service.restore_backup(backup.id, clear_data)

            messages.success(request, _('تم استعادة النسخة الاحتياطية بنجاح.'))
            return redirect('data_management:db_backup_list')
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء استعادة النسخة الاحتياطية: {str(e)}'))
            return redirect('data_management:db_backup_detail', pk=backup.pk)

    context = {
        'backup': backup,
        'title': _('استعادة النسخة الاحتياطية'),
    }

    return render(request, 'data_management/db_manager/backup_restore.html', context)

@login_required
@user_passes_test(is_superuser)
def backup_delete(request, pk):
    """حذف النسخة الاحتياطية"""
    backup = get_object_or_404(DatabaseBackup, pk=pk)

    if request.method == 'POST':
        # حذف ملف النسخة الاحتياطية
        if backup.file:
            file_path = os.path.join(settings.MEDIA_ROOT, backup.file.name)
            if os.path.exists(file_path):
                os.remove(file_path)

        # حذف سجل النسخة الاحتياطية
        backup.delete()

        messages.success(request, _('تم حذف النسخة الاحتياطية بنجاح.'))
        return redirect('data_management:db_backup_list')

    context = {
        'backup': backup,
        'title': _('حذف النسخة الاحتياطية'),
    }

    return render(request, 'data_management/db_manager/backup_delete.html', context)

@login_required
@user_passes_test(is_superuser)
def database_import(request):
    """استيراد قاعدة بيانات"""
    if request.method == 'POST':
        form = DatabaseImportForm(request.POST, request.FILES)
        if form.is_valid():
            # حفظ نموذج الاستيراد
            import_record = form.save(commit=False)
            import_record.status = 'pending'
            import_record.created_by = request.user
            import_record.save()

            try:
                # استيراد قاعدة البيانات
                database_service = DatabaseService(import_record.database_config.id)
                database_service.import_database(
                    import_record.file.path,
                    import_record.database_config,
                    import_record.clear_data,
                    request.user
                )

                # تحديث حالة الاستيراد
                import_record.status = 'completed'
                import_record.completed_at = timezone.now()
                import_record.save()

                messages.success(request, _('تم استيراد قاعدة البيانات بنجاح.'))
                return redirect('data_management:db_import_detail', pk=import_record.pk)
            except Exception as e:
                # تحديث حالة الاستيراد في حالة الخطأ
                import_record.status = 'failed'
                import_record.log = str(e)
                import_record.save()

                messages.error(request, _(f'حدث خطأ أثناء استيراد قاعدة البيانات: {str(e)}'))
                return redirect('data_management:db_import_detail', pk=import_record.pk)
    else:
        form = DatabaseImportForm()

    context = {
        'form': form,
        'title': _('استيراد قاعدة بيانات'),
    }

    return render(request, 'data_management/db_manager/import_form.html', context)

@login_required
@user_passes_test(is_superuser)
def import_detail(request, pk):
    """عرض تفاصيل استيراد قاعدة البيانات"""
    import_record = get_object_or_404(DatabaseImport, pk=pk)

    context = {
        'import_record': import_record,
        'title': _('تفاصيل استيراد قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/import_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def database_export(request):
    """تصدير قاعدة البيانات"""
    if request.method == 'POST':
        # معالجة النموذج
        export_type = request.POST.get('export_type', 'full')
        file_format = request.POST.get('file_format', 'sql')
        compress = request.POST.get('compress', 'off') == 'on'
        encrypt = request.POST.get('encrypt', 'off') == 'on'
        include_media = request.POST.get('include_media', 'off') == 'on'
        tables = request.POST.get('tables', '')

        try:
            # تصدير قاعدة البيانات
            database_config = DatabaseConfig.objects.filter(is_active=True).first()
            if not database_config:
                messages.error(request, _('لا توجد قاعدة بيانات نشطة.'))
                return redirect('data_management:db_export')

            database_service = DatabaseService(database_config.id)
            backup = database_service.create_backup(
                database_config=database_config,
                backup_type=export_type,
                description=f'تصدير يدوي - {export_type} - {file_format}',
                created_by=request.user,
                file_format=file_format,
                compress=compress,
                encrypt=encrypt,
                include_media=include_media,
                tables=tables.split(',') if tables else None
            )

            messages.success(request, _('تم تصدير قاعدة البيانات بنجاح.'))
            return redirect('data_management:db_backup_detail', pk=backup.pk)
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء تصدير قاعدة البيانات: {str(e)}'))
            return redirect('data_management:db_export')

    # الحصول على قائمة قواعد البيانات النشطة
    active_database = DatabaseConfig.objects.filter(is_active=True).first()

    context = {
        'active_database': active_database,
        'title': _('تصدير قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/export.html', context)

@login_required
@user_passes_test(is_superuser)
def setup(request):
    """إعداد النظام"""
    if request.method == 'POST':
        form = DatabaseSetupForm(request.POST, request.FILES)
        if form.is_valid():
            # إنشاء قاعدة بيانات جديدة
            database_config = DatabaseConfig(
                name=form.cleaned_data['name'],
                db_type=form.cleaned_data['db_type'],
                host=form.cleaned_data['host'],
                port=form.cleaned_data['port'],
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                database_name=form.cleaned_data['database_name'],
                is_active=True,
                is_default=True
            )
            database_config.save()

            # إنشاء مستخدم مدير
            User = get_user_model()
            admin_user = User.objects.create_superuser(
                username=form.cleaned_data['admin_username'],
                password=form.cleaned_data['admin_password'],
                email=form.cleaned_data['admin_email']
            )

            # استيراد البيانات إذا تم تحميل ملف
            import_file = form.cleaned_data.get('import_file')
            if import_file:
                try:
                    # إنشاء سجل استيراد
                    import_record = DatabaseImport.objects.create(
                        file=import_file,
                        database_config=database_config,
                        status='pending',
                        clear_data=True,
                        created_by=admin_user
                    )

                    # استيراد البيانات
                    database_service = DatabaseService(database_config.id)
                    database_service.import_database(
                        import_record.file.path,
                        database_config,
                        True,
                        admin_user
                    )

                    # تحديث حالة الاستيراد
                    import_record.status = 'completed'
                    import_record.completed_at = timezone.now()
                    import_record.save()

                    messages.success(request, _('تم استيراد البيانات بنجاح.'))
                except Exception as e:
                    messages.error(request, _(f'حدث خطأ أثناء استيراد البيانات: {str(e)}'))

            messages.success(request, _('تم إعداد النظام بنجاح.'))
            return redirect('data_management:db_dashboard')
    else:
        form = DatabaseSetupForm()

    context = {
        'form': form,
        'title': _('إعداد النظام'),
    }

    return render(request, 'data_management/db_manager/setup.html', context)

@login_required
@user_passes_test(is_superuser)
def setup_with_token(request, token):
    """إعداد النظام باستخدام رمز"""
    # التحقق من صلاحية الرمز
    setup_token = get_object_or_404(SetupToken, token=token, is_used=False, expires_at__gt=timezone.now())

    if request.method == 'POST':
        form = DatabaseSetupForm(request.POST, request.FILES)
        if form.is_valid():
            # إنشاء قاعدة بيانات جديدة
            database_config = DatabaseConfig(
                name=form.cleaned_data['name'],
                db_type=form.cleaned_data['db_type'],
                host=form.cleaned_data['host'],
                port=form.cleaned_data['port'],
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                database_name=form.cleaned_data['database_name'],
                is_active=True,
                is_default=True
            )
            database_config.save()

            # إنشاء مستخدم مدير
            User = get_user_model()
            admin_user = User.objects.create_superuser(
                username=form.cleaned_data['admin_username'],
                password=form.cleaned_data['admin_password'],
                email=form.cleaned_data['admin_email']
            )

            # استيراد البيانات إذا تم تحميل ملف
            import_file = form.cleaned_data.get('import_file')
            if import_file:
                try:
                    # إنشاء سجل استيراد
                    import_record = DatabaseImport.objects.create(
                        file=import_file,
                        database_config=database_config,
                        status='pending',
                        clear_data=True,
                        created_by=admin_user
                    )

                    # استيراد البيانات
                    database_service = DatabaseService(database_config.id)
                    database_service.import_database(
                        import_record.file.path,
                        database_config,
                        True,
                        admin_user
                    )

                    # تحديث حالة الاستيراد
                    import_record.status = 'completed'
                    import_record.completed_at = timezone.now()
                    import_record.save()

                    messages.success(request, _('تم استيراد البيانات بنجاح.'))
                except Exception as e:
                    messages.error(request, _(f'حدث خطأ أثناء استيراد البيانات: {str(e)}'))

            # تحديث حالة الرمز
            setup_token.is_used = True
            setup_token.save()

            messages.success(request, _('تم إعداد النظام بنجاح.'))
            return redirect('data_management:db_dashboard')
    else:
        form = DatabaseSetupForm()

    context = {
        'form': form,
        'token': token,
        'title': _('إعداد النظام'),
    }

    return render(request, 'data_management/db_manager/setup_with_token.html', context)

@login_required
@user_passes_test(is_superuser)
def create_setup_token(request):
    """إنشاء رمز إعداد"""
    if request.method == 'POST':
        form = SetupTokenForm(request.POST)
        if form.is_valid():
            # إنشاء رمز إعداد
            token = form.save()

            # إنشاء رابط الإعداد
            database_service = DatabaseService()
            setup_url = request.build_absolute_uri(database_service.get_setup_url(token))

            messages.success(request, _('تم إنشاء رمز الإعداد بنجاح.'))

            context = {
                'token': token,
                'setup_url': setup_url,
                'title': _('رمز الإعداد'),
            }

            return render(request, 'data_management/db_manager/setup_token_created.html', context)
    else:
        form = SetupTokenForm()

    context = {
        'form': form,
        'title': _('إنشاء رمز إعداد'),
    }

    return render(request, 'data_management/db_manager/setup_token_form.html', context)
