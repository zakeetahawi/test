"""
وجهات نظر وحدة إدارة قواعد البيانات
"""

import os
import traceback
import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connections

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
    setup_token_count = setup_tokens.count()

    context = {
        'database_count': database_count,
        'active_database': active_database,
        'default_database': default_database,
        'backup_count': backup_count,
        'recent_backups': recent_backups,
        'import_count': import_count,
        'recent_imports': recent_imports,
        'setup_tokens': setup_tokens,
        'setup_token_count': setup_token_count,
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
    # تعطيل المعاملات الذرية لهذه الوظيفة
    database_create.atomic = False

    if request.method == 'POST':
        form = DatabaseConfigForm(request.POST)
        if form.is_valid():
            database = form.save()

            # إضافة إعدادات قاعدة البيانات إلى الملف الخارجي
            from data_management.db_settings import add_database_settings

            # إنشاء إعدادات قاعدة البيانات
            db_settings = {
                'ENGINE': f"django.db.backends.{database.db_type}",
                'NAME': database.database_name,
                'USER': database.username,
                'PASSWORD': database.password,
                'HOST': database.host,
                'PORT': database.port,
            }

            # إضافة إعدادات قاعدة البيانات
            add_database_settings(database.id, db_settings)

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
    # تعطيل المعاملات الذرية لهذه الوظيفة
    database_update.atomic = False

    database = get_object_or_404(DatabaseConfig, pk=pk)

    if request.method == 'POST':
        form = DatabaseConfigForm(request.POST, instance=database)
        if form.is_valid():
            database = form.save()

            # تحديث إعدادات قاعدة البيانات في الملف الخارجي
            from data_management.db_settings import add_database_settings

            # إنشاء إعدادات قاعدة البيانات
            db_settings = {
                'ENGINE': f"django.db.backends.{database.db_type}",
                'NAME': database.database_name,
                'USER': database.username,
                'PASSWORD': database.password,
                'HOST': database.host,
                'PORT': database.port,
            }

            # تحديث إعدادات قاعدة البيانات
            add_database_settings(database.id, db_settings)

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
    # تعطيل المعاملات الذرية لهذه الوظيفة
    database_delete.atomic = False

    database = get_object_or_404(DatabaseConfig, pk=pk)

    # منع حذف قاعدة البيانات النشطة
    if database.is_active:
        messages.error(request, _('لا يمكن حذف قاعدة البيانات النشطة. قم بتنشيط قاعدة بيانات أخرى أولاً.'))
        return redirect('data_management:database_list')

    if request.method == 'POST':
        # تخزين معلومات قاعدة البيانات قبل الحذف
        is_default = database.is_default

        # حذف إعدادات قاعدة البيانات من الملف الخارجي
        from data_management.db_settings import remove_database_settings
        remove_database_settings(database.id)

        # حذف قاعدة البيانات
        database.delete()

        # إذا كانت قاعدة البيانات المحذوفة هي الافتراضية، قم بتعيين قاعدة بيانات أخرى كافتراضية
        if is_default:
            other_db = DatabaseConfig.objects.first()
            if other_db:
                other_db.is_default = True
                other_db.save()

        # تنظيف ذاكرة التخزين المؤقت
        from django.core.cache import cache
        cache.clear()

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
    # تعطيل المعاملات الذرية لهذه الوظيفة
    database_set_default.atomic = False

    database = get_object_or_404(DatabaseConfig, pk=pk)

    if request.method == 'POST':
        # تعيين قاعدة البيانات كافتراضية
        # سيقوم نموذج DatabaseConfig.save() تلقائيًا بإلغاء تعيين قواعد البيانات الأخرى كافتراضية
        database.is_default = True
        database.save()

        # تنظيف ذاكرة التخزين المؤقت
        from django.core.cache import cache
        cache.clear()

        messages.success(request, _('تم تعيين قاعدة البيانات كافتراضية بنجاح.'))

        # إعادة توجيه إلى قائمة قواعد البيانات بدلاً من تفاصيل قاعدة البيانات
        # لضمان رؤية التغييرات
        return redirect('data_management:database_list')

    context = {
        'database': database,
        'title': _('تعيين قاعدة البيانات كافتراضية'),
    }

    return render(request, 'data_management/db_manager/database_set_default.html', context)

@login_required
@user_passes_test(is_superuser)
def database_set_active(request, pk):
    """تنشيط قاعدة البيانات"""
    # تعطيل المعاملات الذرية لهذه الوظيفة
    database_set_active.atomic = False

    database = get_object_or_404(DatabaseConfig, pk=pk)

    if request.method == 'POST':
        try:
            # إلغاء تنشيط جميع قواعد البيانات الأخرى
            DatabaseConfig.objects.all().update(is_active=False)

            # تنشيط قاعدة البيانات المحددة
            database.is_active = True
            database.save()

            # تنظيف ذاكرة التخزين المؤقت
            from django.core.cache import cache
            cache.clear()

            # تحديث ملف إعدادات قاعدة البيانات الخارجي
            from data_management.db_settings import set_active_database, add_database_settings

            # إنشاء إعدادات قاعدة البيانات
            db_settings = {
                'ENGINE': f"django.db.backends.{database.db_type}",
                'NAME': database.database_name,
                'USER': database.username,
                'PASSWORD': database.password,
                'HOST': database.host,
                'PORT': database.port,
            }

            # إضافة إعدادات قاعدة البيانات
            add_database_settings(database.id, db_settings)

            # تعيين قاعدة البيانات النشطة
            set_active_database(database.id)

            messages.success(request, _('تم تنشيط قاعدة البيانات بنجاح. يرجى إعادة تشغيل الخادم لتطبيق التغييرات.'))

            # إعادة توجيه إلى صفحة إعادة تحميل التطبيق
            return redirect('data_management:database_reload')
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء تنشيط قاعدة البيانات: {str(e)}'))
            return redirect('data_management:database_list')

    context = {
        'database': database,
        'title': _('تنشيط قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/database_set_active.html', context)

@login_required
@user_passes_test(is_superuser)
def database_reload(request):
    """إعادة تحميل التطبيق بعد تبديل قاعدة البيانات"""
    # تعطيل المعاملات الذرية لهذه الوظيفة
    database_reload.atomic = False

    context = {
        'title': _('إعادة تحميل التطبيق'),
    }

    return render(request, 'data_management/db_manager/database_reload.html', context)

@login_required
@user_passes_test(is_superuser)
def reset_database_settings(request):
    """إعادة تعيين إعدادات قاعدة البيانات إلى الإعدادات الافتراضية"""
    # تعطيل المعاملات الذرية لهذه الوظيفة
    reset_database_settings.atomic = False

    if request.method == 'POST':
        try:
            # إعادة تعيين إعدادات قاعدة البيانات إلى الإعدادات الافتراضية
            from data_management.db_settings import reset_to_default_settings
            reset_to_default_settings()

            messages.success(request, _('تم إعادة تعيين إعدادات قاعدة البيانات إلى الإعدادات الافتراضية بنجاح.'))

            # تعيين متغير البيئة RESET_DB لإعادة تعيين إعدادات قاعدة البيانات عند إعادة تشغيل الخادم
            os.environ['RESET_DB'] = '1'

            # إعادة توجيه إلى صفحة إعادة تحميل التطبيق
            return redirect('data_management:database_reload')
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء إعادة تعيين إعدادات قاعدة البيانات: {str(e)}'))
            return redirect('data_management:database_list')

    context = {
        'title': _('إعادة تعيين إعدادات قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/reset_database_settings.html', context)

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
                return redirect('data_management:db_manager:db_backup_detail', pk=backup.pk)
            except Exception as e:
                messages.error(request, _(f'حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}'))
                return redirect('data_management:db_manager:db_backup_create')
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
        return redirect('data_management:db_manager:db_backup_detail', pk=backup.pk)

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
            return redirect('data_management:db_manager:db_backup_list')
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء استعادة النسخة الاحتياطية: {str(e)}'))
            return redirect('data_management:db_manager:db_backup_detail', pk=backup.pk)

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
        return redirect('data_management:db_manager:db_backup_list')

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

                # تحديد خيارات الاستيراد
                import_options = {
                    'file_path': import_record.file.path,
                    'database_config': import_record.database_config,
                    'user': request.user,
                    'clear_data': import_record.clear_data,
                }

                # إضافة خيارات الاستيراد الانتقائي من النموذج
                import_mode = form.cleaned_data.get('import_mode', 'merge')
                if import_mode == 'selective':
                    import_options.update({
                        'import_mode': 'selective',
                        'import_settings': form.cleaned_data.get('import_settings', True),
                        'import_users': form.cleaned_data.get('import_users', False),
                        'import_customers': form.cleaned_data.get('import_customers', True),
                        'import_products': form.cleaned_data.get('import_products', True),
                        'import_orders': form.cleaned_data.get('import_orders', True),
                        'import_inspections': form.cleaned_data.get('import_inspections', True),
                        'conflict_resolution': form.cleaned_data.get('conflict_resolution', 'skip'),
                    })
                else:
                    import_options.update({
                        'import_mode': import_mode,
                        'conflict_resolution': form.cleaned_data.get('conflict_resolution', 'skip'),
                    })

                # بدء عملية الاستيراد في خلفية منفصلة
                import threading

                def import_task():
                    try:
                        # تحديث حالة الاستيراد
                        import_record.status = 'processing'
                        import_record.log = 'بدء عملية استيراد البيانات...\n'
                        import_record.save()

                        # استيراد البيانات
                        result = database_service.import_database_advanced(**import_options)

                        # تحديث إحصائيات الاستيراد
                        import_record.total_records = result.get('total_records', 0)
                        import_record.imported_records = result.get('imported_records', 0)
                        import_record.skipped_records = result.get('skipped_records', 0)
                        import_record.failed_records = result.get('failed_records', 0)

                        # تحديث حالة الاستيراد
                        import_record.status = 'completed'
                        import_record.completed_at = timezone.now()
                        import_record.log += '\nاكتملت عملية الاستيراد بنجاح.\n'
                        import_record.log += f'\nإجمالي السجلات: {import_record.total_records}\n'
                        import_record.log += f'السجلات المستوردة: {import_record.imported_records}\n'
                        import_record.log += f'السجلات المتخطاة: {import_record.skipped_records}\n'
                        import_record.log += f'السجلات الفاشلة: {import_record.failed_records}\n'
                        import_record.save()
                    except Exception as e:
                        # تحديث حالة الاستيراد في حالة الخطأ
                        import_record.status = 'failed'
                        import_record.log += f'\n❌ فشلت العملية بسبب الخطأ التالي:\n{str(e)}\n'
                        import_record.log += f'\n🔍 تفاصيل الخطأ:\n{traceback.format_exc()}\n'
                        import_record.log += '\n💡 اقتراحات للإصلاح:\n'
                        import_record.log += '- تأكد من صحة تنسيق ملف الاستيراد.\n'
                        import_record.log += '- تأكد من توافق إصدار قاعدة البيانات.\n'
                        import_record.log += '- تحقق من صلاحيات المستخدم.\n'
                        import_record.save()

                # بدء العملية في خلفية منفصلة
                thread = threading.Thread(target=import_task)
                thread.daemon = True
                thread.start()

                messages.success(request, _('تم بدء عملية استيراد البيانات بنجاح. يمكنك متابعة حالة الاستيراد من صفحة التفاصيل.'))
                return redirect('data_management:db_manager:import_status', pk=import_record.pk)
            except Exception as e:
                # تحديث حالة الاستيراد في حالة الخطأ
                import_record.status = 'failed'
                import_record.log = f'❌ فشلت العملية بسبب الخطأ التالي:\n{str(e)}\n'
                import_record.save()

                messages.error(request, _(f'حدث خطأ أثناء بدء عملية استيراد البيانات: {str(e)}'))
                return redirect('data_management:db_manager:import_detail', pk=import_record.pk)
    else:
        form = DatabaseImportForm()

    # الحصول على قائمة قواعد البيانات النشطة
    active_databases = DatabaseConfig.objects.filter(is_active=True)

    context = {
        'form': form,
        'title': _('استيراد قاعدة بيانات'),
        'active_databases': active_databases,
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
def import_status(request, pk):
    """عرض حالة عملية الاستيراد"""
    try:
        db_import = get_object_or_404(DatabaseImport, pk=pk)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # استجابة AJAX لتحديث الحالة
            try:
                # تحليل السجل لاستخراج معلومات إضافية
                log = db_import.log or ''
                progress_info = analyze_import_log(log, db_import.status)

                # إعداد البيانات للاستجابة
                response_data = {
                    'status': db_import.status,
                    'completed_at': db_import.completed_at.isoformat() if db_import.completed_at else None,
                    'log': log,
                    'progress': progress_info['progress'],
                    'current_step': progress_info['current_step'],
                    'total_steps': progress_info['total_steps'],
                    'estimated_time_remaining': progress_info['estimated_time_remaining'],
                    'file_info': {
                        'name': os.path.basename(db_import.file.name) if db_import.file else '',
                        'size': db_import.file.size if db_import.file else 0,
                    },
                    'database_info': {
                        'name': db_import.database_config.name,
                        'type': db_import.database_config.get_db_type_display(),
                    },
                    'created_at': db_import.created_at.isoformat(),
                    'duration': (db_import.completed_at - db_import.created_at).total_seconds() if db_import.completed_at else (timezone.now() - db_import.created_at).total_seconds(),
                }

                # إضافة معلومات الخطأ إذا كانت العملية فاشلة
                if db_import.status == 'failed':
                    error_info = extract_error_info(log)
                    response_data.update({
                        'error_message': error_info['message'],
                        'error_details': error_info['details'],
                        'error_suggestions': error_info['suggestions'],
                    })

                return JsonResponse(response_data)
            except Exception as e:
                # في حالة حدوث خطأ في استجابة AJAX
                return JsonResponse({
                    'status': 'error',
                    'error': str(e),
                    'log': db_import.log or '',
                })

        return render(request, 'data_management/db_manager/import_status.html', {
            'db_import': db_import,
        })
    except Exception as e:
        # في حالة حدوث خطأ غير متوقع
        messages.error(request, _('حدث خطأ أثناء عرض حالة الاستيراد: {}').format(str(e)))

        # تسجيل الخطأ
        import traceback
        traceback.print_exc()

        # إعادة توجيه المستخدم إلى صفحة لوحة التحكم
        return redirect('data_management:db_manager:db_dashboard')


def analyze_import_log(log, status):
    """تحليل سجل الاستيراد لاستخراج معلومات التقدم"""
    result = {
        'progress': 0,
        'current_step': '',
        'total_steps': 5,  # عدد الخطوات الافتراضي
        'estimated_time_remaining': None,
    }

    if not log:
        return result

    # تحديد الخطوات الرئيسية في عملية الاستيراد
    steps = [
        {'keyword': 'بدء عملية استيراد', 'weight': 5, 'step': 'بدء الاستيراد'},
        {'keyword': 'إنشاء نسخة احتياطية', 'weight': 10, 'step': 'إنشاء نسخة احتياطية'},
        {'keyword': 'جاري التحضير لعملية الاستيراد', 'weight': 20, 'step': 'تحضير الاستيراد'},
        {'keyword': 'بدء استيراد ملف', 'weight': 30, 'step': 'استيراد البيانات'},
        {'keyword': 'تم استيراد البيانات', 'weight': 80, 'step': 'اكتمال الاستيراد'},
        {'keyword': 'التحقق من البيانات المكررة', 'weight': 90, 'step': 'التحقق من البيانات'},
        {'keyword': 'اكتملت العملية بنجاح', 'weight': 100, 'step': 'اكتمال العملية'},
    ]

    # تحديد الخطوة الحالية والتقدم
    current_progress = 0
    current_step = 'بدء الاستيراد'

    for step in steps:
        if step['keyword'] in log:
            current_progress = step['weight']
            current_step = step['step']

    # تعديل التقدم بناءً على الحالة
    if status == 'completed':
        current_progress = 100
        current_step = 'اكتمال العملية'
    elif status == 'failed':
        current_step = 'فشل العملية'

    # تقدير الوقت المتبقي (تقريبي جدًا)
    estimated_time_remaining = None
    if status == 'in_progress' and current_progress > 0 and current_progress < 100:
        # تقدير بسيط: إذا كان التقدم 50% والوقت المنقضي 5 دقائق، فالوقت المتبقي 5 دقائق أيضًا
        # هذا تقدير بسيط جدًا ويمكن تحسينه بتحليل أكثر تعقيدًا
        estimated_time_remaining = "غير معروف"

    result['progress'] = current_progress
    result['current_step'] = current_step
    result['estimated_time_remaining'] = estimated_time_remaining

    return result


def extract_error_info(log):
    """استخراج معلومات الخطأ من سجل الاستيراد"""
    result = {
        'message': '',
        'details': '',
        'suggestions': [],
    }

    if not log:
        return result

    # استخراج رسالة الخطأ
    error_marker = "❌ فشلت العملية بسبب الخطأ التالي:"
    details_marker = "🔍 تفاصيل الخطأ:"
    suggestions_marker = "💡 اقتراحات للإصلاح:"

    if error_marker in log:
        error_section = log.split(error_marker)[1].split(details_marker)[0].strip()
        result['message'] = error_section

    if details_marker in log:
        details_section = log.split(details_marker)[1].split(suggestions_marker)[0].strip()
        result['details'] = details_section

    if suggestions_marker in log:
        suggestions_section = log.split(suggestions_marker)[1].strip()
        suggestions = [s.strip() for s in suggestions_section.split('\n') if s.strip() and s.strip().startswith('-')]
        result['suggestions'] = suggestions

    return result


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
                return redirect('data_management:db_manager:db_export')

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
            return redirect('data_management:db_manager:db_backup_detail', pk=backup.pk)
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء تصدير قاعدة البيانات: {str(e)}'))
            return redirect('data_management:db_manager:db_export')

    # الحصول على قائمة قواعد البيانات النشطة
    active_database = DatabaseConfig.objects.filter(is_active=True).first()

    context = {
        'active_database': active_database,
        'title': _('تصدير قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/export.html', context)

@login_required
@user_passes_test(is_superuser)
def test_current_database_connection(request):
    """اختبار الاتصال بقاعدة البيانات الحالية"""
    # تعطيل المعاملات الذرية لهذه الوظيفة
    test_current_database_connection.atomic = False

    # استخدام معلمة الطلب لتسجيل المستخدم الذي قام بالاختبار
    user_id = request.user.id if request.user.is_authenticated else None

    success = False
    message = ""
    db_info = {
        'user_id': user_id
    }

    try:
        # الحصول على معلومات قاعدة البيانات الحالية من الإعدادات
        from django.conf import settings
        db_settings = settings.DATABASES['default']

        # استخراج معلومات الاتصال
        db_info = {
            'engine': db_settings.get('ENGINE', '').split('.')[-1],
            'name': db_settings.get('NAME', ''),
            'user': db_settings.get('USER', ''),
            'host': db_settings.get('HOST', ''),
            'port': db_settings.get('PORT', ''),
        }

        # اختبار الاتصال باستخدام Django
        connection = connections['default']
        connection.ensure_connection()

        # إذا وصلنا إلى هنا، فإن الاتصال ناجح
        success = True
        message = _('تم الاتصال بقاعدة البيانات بنجاح.')

        # إضافة معلومات إضافية
        if 'postgresql' in db_info['engine'].lower():
            # الحصول على معلومات إضافية من PostgreSQL
            with connection.cursor() as cursor:
                # الحصول على إصدار قاعدة البيانات
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                db_info['version'] = version

                # الحصول على حجم قاعدة البيانات
                cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
                """)
                size = cursor.fetchone()[0]
                db_info['size'] = size

                # الحصول على عدد الجداول
                cursor.execute("""
                SELECT count(*) FROM information_schema.tables
                WHERE table_schema = 'public';
                """)
                tables_count = cursor.fetchone()[0]
                db_info['tables_count'] = tables_count
    except Exception as e:
        success = False
        message = str(e)

    return JsonResponse({
        'success': success,
        'message': message,
        'db_info': db_info
    })

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

            # إنشاء مستخدم مدير (أو استخدام المستخدم الموجود)
            User = get_user_model()
            admin_username = form.cleaned_data['admin_username']

            # التحقق من وجود المستخدم
            try:
                admin_user = User.objects.get(username=admin_username)
                # تحديث كلمة المرور والبريد الإلكتروني إذا كان المستخدم موجودًا
                admin_user.set_password(form.cleaned_data['admin_password'])
                admin_user.email = form.cleaned_data['admin_email']
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.save()
                messages.info(request, _(f'تم تحديث بيانات المستخدم {admin_username} الموجود.'))
            except User.DoesNotExist:
                # إنشاء مستخدم جديد إذا لم يكن موجودًا
                admin_user = User.objects.create_superuser(
                    username=admin_username,
                    password=form.cleaned_data['admin_password'],
                    email=form.cleaned_data['admin_email']
                )
                messages.success(request, _(f'تم إنشاء المستخدم {admin_username} بنجاح.'))

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
