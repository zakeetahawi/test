@login_required
@user_passes_test(is_superuser)
def db_export(request):
    """تصدير قاعدة البيانات"""
    if request.method == 'POST':
        form = DatabaseBackupForm(request.POST)
        if form.is_valid():
            # الحصول على البيانات من النموذج
            database_config = form.cleaned_data['database_config']
            backup_type = form.cleaned_data['backup_type']
            description = form.cleaned_data['description']

            try:
                # التحقق من وجود قاعدة بيانات نشطة
                if not database_config:
                    messages.error(request, _('لا توجد قاعدة بيانات نشطة.'))
                    return redirect('data_management:db_manager:db_export')

                # إنشاء النسخة الاحتياطية
                database_service = DatabaseService(database_config.id)
                backup = database_service.create_backup(
                    database_config=database_config,
                    backup_type=backup_type,
                    description=description,
                    created_by=request.user
                )

                messages.success(request, _('تم تصدير قاعدة البيانات بنجاح.'))
                return redirect('data_management:db_manager:db_backup_detail', pk=backup.pk)
            except Exception as e:
                messages.error(request, _(f'حدث خطأ أثناء تصدير قاعدة البيانات: {str(e)}'))
                return redirect('data_management:db_manager:db_export')
    else:
        form = DatabaseBackupForm()

    context = {
        'form': form,
        'title': _('تصدير قاعدة البيانات'),
    }

    return render(request, 'data_management/db_manager/export_form.html', context)

@login_required
@user_passes_test(is_superuser)
def test_connection(request):
    """اختبار الاتصال بقاعدة البيانات"""
    if request.method == 'POST':
        form = DatabaseConfigForm(request.POST)
        if form.is_valid():
            # الحصول على البيانات من النموذج
            db_type = form.cleaned_data['db_type']
            host = form.cleaned_data['host']
            port = form.cleaned_data['port']
            database_name = form.cleaned_data['database_name']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                # إنشاء اتصال مؤقت بقاعدة البيانات
                if db_type == 'postgresql':
                    import psycopg2
                    conn = psycopg2.connect(
                        host=host,
                        port=port,
                        database=database_name,
                        user=username,
                        password=password
                    )
                    conn.close()
                elif db_type == 'mysql':
                    import mysql.connector
                    conn = mysql.connector.connect(
                        host=host,
                        port=port,
                        database=database_name,
                        user=username,
                        password=password
                    )
                    conn.close()
                elif db_type == 'sqlite3':
                    import sqlite3
                    conn = sqlite3.connect(database_name)
                    conn.close()
                else:
                    return JsonResponse({'success': False, 'message': _('نوع قاعدة البيانات غير مدعوم.')})

                return JsonResponse({'success': True, 'message': _('تم الاتصال بقاعدة البيانات بنجاح.')})
            except Exception as e:
                return JsonResponse({'success': False, 'message': _(f'فشل الاتصال بقاعدة البيانات: {str(e)}')})
        else:
            return JsonResponse({'success': False, 'message': _('البيانات المدخلة غير صحيحة.')})
    else:
        return JsonResponse({'success': False, 'message': _('طريقة الطلب غير صحيحة.')})

@login_required
@user_passes_test(is_superuser)
def create_setup_token(request):
    """إنشاء رمز إعداد جديد"""
    if request.method == 'POST':
        form = SetupTokenForm(request.POST)
        if form.is_valid():
            # إنشاء رمز إعداد جديد
            token = form.save(commit=False)
            token.created_by = request.user
            token.save()

            messages.success(request, _('تم إنشاء رمز الإعداد بنجاح.'))
            return redirect('data_management:db_manager:db_dashboard')
    else:
        form = SetupTokenForm()

    context = {
        'form': form,
        'title': _('إنشاء رمز إعداد جديد'),
    }

    return render(request, 'data_management/db_manager/setup_token_form.html', context)

@login_required
@user_passes_test(is_superuser)
def setup_token_list(request):
    """عرض قائمة رموز الإعداد"""
    tokens = SetupToken.objects.all().order_by('-created_at')

    # تصفية النتائج
    is_used = request.GET.get('is_used')
    is_expired = request.GET.get('is_expired')

    if is_used:
        tokens = tokens.filter(is_used=is_used == 'true')

    if is_expired:
        if is_expired == 'true':
            tokens = tokens.filter(expires_at__lt=timezone.now())
        else:
            tokens = tokens.filter(expires_at__gte=timezone.now())

    # ترقيم الصفحات
    paginator = Paginator(tokens, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_used': is_used,
        'is_expired': is_expired,
        'title': _('قائمة رموز الإعداد'),
    }

    return render(request, 'data_management/db_manager/setup_token_list.html', context)

@login_required
@user_passes_test(is_superuser)
def setup_token_delete(request, pk):
    """حذف رمز إعداد"""
    token = get_object_or_404(SetupToken, pk=pk)

    if request.method == 'POST':
        # حذف رمز الإعداد
        token.delete()

        messages.success(request, _('تم حذف رمز الإعداد بنجاح.'))
        return redirect('data_management:db_manager:setup_token_list')

    context = {
        'token': token,
        'title': _('حذف رمز الإعداد'),
    }

    return render(request, 'data_management/db_manager/setup_token_delete.html', context)

def setup(request, token):
    """إعداد النظام باستخدام رمز الإعداد"""
    # التحقق من صحة الرمز
    setup_token = get_object_or_404(SetupToken, token=token, is_used=False, expires_at__gt=timezone.now())

    if request.method == 'POST':
        form = DatabaseSetupForm(request.POST)
        if form.is_valid():
            try:
                # إنشاء قاعدة بيانات جديدة
                database_config = DatabaseConfig.objects.create(
                    name=form.cleaned_data['name'],
                    db_type=form.cleaned_data['db_type'],
                    host=form.cleaned_data['host'],
                    port=form.cleaned_data['port'],
                    database_name=form.cleaned_data['database_name'],
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password'],
                    is_default=True,
                    is_active=True
                )

                # إضافة إعدادات قاعدة البيانات إلى الملف الخارجي
                from data_management.db_settings import add_database_settings, set_active_database

                # إنشاء إعدادات قاعدة البيانات
                db_settings = {
                    'ENGINE': f"django.db.backends.{database_config.db_type}",
                    'NAME': database_config.database_name,
                    'USER': database_config.username,
                    'PASSWORD': database_config.password,
                    'HOST': database_config.host,
                    'PORT': database_config.port,
                }

                # إضافة إعدادات قاعدة البيانات
                add_database_settings(database_config.id, db_settings)

                # تعيين قاعدة البيانات النشطة
                set_active_database(database_config.id)

                # إنشاء مستخدم مدير
                User = get_user_model()
                if not User.objects.filter(is_superuser=True).exists():
                    User.objects.create_superuser(
                        username=form.cleaned_data['admin_username'],
                        email=form.cleaned_data['admin_email'],
                        password=form.cleaned_data['admin_password']
                    )

                # تحديث رمز الإعداد
                setup_token.is_used = True
                setup_token.save()

                messages.success(request, _('تم إعداد النظام بنجاح.'))
                return redirect('data_management:db_manager:db_dashboard')
            except Exception as e:
                messages.error(request, _(f'حدث خطأ أثناء إعداد النظام: {str(e)}'))
    else:
        form = DatabaseSetupForm()

    context = {
        'form': form,
        'token': setup_token,
        'title': _('إعداد النظام'),
    }

    return render(request, 'data_management/db_manager/setup.html', context)
