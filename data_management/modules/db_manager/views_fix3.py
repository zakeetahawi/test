@login_required
@user_passes_test(is_superuser)
def backup_restore(request, pk):
    """استعادة النسخة الاحتياطية"""
    backup = get_object_or_404(DatabaseBackup, pk=pk)

    if request.method == 'POST':
        try:
            # استعادة النسخة الاحتياطية
            database_service = DatabaseService(backup.database_config.id)
            database_service.restore_backup(backup)

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
        if backup.file and os.path.exists(os.path.join(settings.MEDIA_ROOT, backup.file.name)):
            os.remove(os.path.join(settings.MEDIA_ROOT, backup.file.name))

        # حذف النسخة الاحتياطية
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
def db_import(request):
    """استيراد قاعدة بيانات"""
    if request.method == 'POST':
        form = DatabaseImportForm(request.POST, request.FILES)
        if form.is_valid():
            # الحصول على البيانات من النموذج
            database_config = form.cleaned_data['database_config']
            file = form.cleaned_data['file']
            clear_data = form.cleaned_data.get('clear_data', False)

            # إنشاء سجل استيراد
            import_record = DatabaseImport.objects.create(
                file=file,
                database_config=database_config,
                status='pending',
                clear_data=clear_data,
                created_by=request.user
            )

            try:
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

                # بدء عملية الاستيراد في خلفية
                database_service = DatabaseService(database_config.id)
                thread = threading.Thread(
                    target=database_service.import_database,
                    kwargs={
                        'import_record': import_record,
                        'options': import_options
                    }
                )
                thread.daemon = True
                thread.start()

                messages.success(request, _('تم بدء عملية الاستيراد بنجاح. يمكنك متابعة التقدم من خلال صفحة التفاصيل.'))
                return redirect('data_management:db_manager:db_import_detail', pk=import_record.pk)
            except Exception as e:
                import_record.status = 'failed'
                import_record.log = str(e)
                import_record.save()
                messages.error(request, _(f'حدث خطأ أثناء بدء عملية الاستيراد: {str(e)}'))
                return redirect('data_management:db_manager:db_import')
    else:
        form = DatabaseImportForm()

    context = {
        'form': form,
        'title': _('استيراد قاعدة بيانات'),
    }

    return render(request, 'data_management/db_manager/import_form.html', context)

@login_required
@user_passes_test(is_superuser)
def db_import_detail(request, pk):
    """عرض تفاصيل عملية الاستيراد"""
    import_record = get_object_or_404(DatabaseImport, pk=pk)

    context = {
        'import': import_record,
        'title': _('تفاصيل عملية الاستيراد'),
    }

    return render(request, 'data_management/db_manager/import_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def db_import_status(request, pk):
    """الحصول على حالة عملية الاستيراد"""
    import_record = get_object_or_404(DatabaseImport, pk=pk)

    data = {
        'status': import_record.status,
        'log': import_record.log,
        'total_records': import_record.total_records,
        'imported_records': import_record.imported_records,
        'skipped_records': import_record.skipped_records,
        'failed_records': import_record.failed_records,
    }

    return JsonResponse(data)

@login_required
@user_passes_test(is_superuser)
def db_import_list(request):
    """عرض قائمة عمليات الاستيراد"""
    imports = DatabaseImport.objects.all().order_by('-created_at')

    # تصفية النتائج
    database_id = request.GET.get('database_id')
    status = request.GET.get('status')

    if database_id:
        imports = imports.filter(database_config_id=database_id)

    if status:
        imports = imports.filter(status=status)

    # ترقيم الصفحات
    paginator = Paginator(imports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # الحصول على قائمة قواعد البيانات
    databases = DatabaseConfig.objects.all()

    context = {
        'page_obj': page_obj,
        'databases': databases,
        'database_id': database_id,
        'status': status,
        'title': _('قائمة عمليات الاستيراد'),
    }

    return render(request, 'data_management/db_manager/import_list.html', context)

@login_required
@user_passes_test(is_superuser)
def db_import_delete(request, pk):
    """حذف عملية استيراد"""
    import_record = get_object_or_404(DatabaseImport, pk=pk)

    if request.method == 'POST':
        # حذف ملف الاستيراد
        if import_record.file and os.path.exists(os.path.join(settings.MEDIA_ROOT, import_record.file.name)):
            os.remove(os.path.join(settings.MEDIA_ROOT, import_record.file.name))

        # حذف سجل الاستيراد
        import_record.delete()

        messages.success(request, _('تم حذف عملية الاستيراد بنجاح.'))
        return redirect('data_management:db_manager:db_import_list')

    context = {
        'import': import_record,
        'title': _('حذف عملية الاستيراد'),
    }

    return render(request, 'data_management/db_manager/import_delete.html', context)
