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
            return redirect('data_management:db_manager:database_reload')
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء تنشيط قاعدة البيانات: {str(e)}'))
            return redirect('data_management:db_manager:database_list')

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
            return redirect('data_management:db_manager:database_reload')
        except Exception as e:
            messages.error(request, _(f'حدث خطأ أثناء إعادة تعيين إعدادات قاعدة البيانات: {str(e)}'))
            return redirect('data_management:db_manager:database_list')

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
