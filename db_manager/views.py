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


def is_superuser(user):
    """التحقق مما إذا كان المستخدم مسؤولاً"""
    return user.is_superuser


def cleanup_old_imports():
    """تنظيف سجلات الاستيراد القديمة"""
    from datetime import timedelta
    from django.utils import timezone
    from django.db import connection

    try:
        # حذف جميع سجلات الاستيراد القديمة التي فشلت أو اكتملت منذ أكثر من يوم
        one_day_ago = timezone.now() - timedelta(days=1)

        # الحصول على سجلات الاستيراد القديمة
        old_imports = DatabaseImport.objects.filter(
            status__in=['failed', 'completed'],
            created_at__lt=one_day_ago
        )

        # حذف السجلات القديمة
        for old_import in old_imports:
            try:
                # حذف الملف أولاً
                if old_import.file:
                    old_import.file.delete(save=False)
                # ثم حذف السجل
                old_import.delete()
            except Exception as e:
                # تسجيل الخطأ ولكن متابعة العملية
                print(f"Error deleting old import: {e}")

        # التحقق من وجود سجلات استيراد عالقة (في حالة "قيد التنفيذ" لأكثر من ساعة)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        stuck_imports = DatabaseImport.objects.filter(
            status='in_progress',
            created_at__lt=one_hour_ago
        )

        # تحديث حالة السجلات العالقة إلى "فشل"
        for stuck_import in stuck_imports:
            try:
                stuck_import.status = 'failed'
                stuck_import.log = (stuck_import.log or '') + '\nتم إلغاء العملية بسبب استمرارها لفترة طويلة دون اكتمال.'
                stuck_import.save()
            except Exception as e:
                # تسجيل الخطأ ولكن متابعة العملية
                print(f"Error updating stuck import: {e}")

        # إعادة ضبط تسلسل المعرفات في قاعدة البيانات إذا لم تكن هناك سجلات
        if not DatabaseImport.objects.exists():
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT setval('db_manager_databaseimport_id_seq', 1, false);")
            except Exception as e:
                # تسجيل الخطأ ولكن متابعة العملية
                print(f"Error resetting database sequence: {e}")
    except Exception as e:
        # تسجيل الخطأ الرئيسي
        print(f"Error in cleanup_old_imports: {e}")


def setup_view(request):
    """صفحة الإعداد الأولي للنظام"""
    try:
        # التحقق مما إذا كان النظام مُعدًا بالفعل
        if DatabaseConfig.objects.filter(is_active=True).exists():
            # إذا كان هناك قاعدة بيانات نشطة، فإن النظام مُعد بالفعل
            # توجيه المستخدم إلى صفحة تسجيل الدخول
            messages.info(request, _('النظام مُعد بالفعل. يرجى تسجيل الدخول.'))
            return redirect('accounts:login')

        # إنشاء رمز إعداد جديد
        token = SetupToken.objects.create(
            expires_at=timezone.now() + timedelta(hours=24)
        )

        setup_url = request.build_absolute_uri(
            reverse('db_manager:setup_with_token', args=[token.token])
        )

        return render(request, 'db_manager/setup.html', {
            'token': token,
            'setup_url': setup_url,
        })
    except Exception as e:
        # في حالة حدوث خطأ (مثل عدم وجود جدول قاعدة البيانات)
        # إنشاء صفحة إعداد بسيطة
        from django.contrib.auth.models import User

        # التحقق من وجود مستخدمين
        try:
            has_users = User.objects.exists()
        except:
            has_users = False

        # إنشاء نموذج إعداد بسيط
        if request.method == 'POST':
            # معالجة النموذج
            db_type = request.POST.get('db_type', 'postgresql')
            host = request.POST.get('host', 'localhost')
            port = request.POST.get('port', '5432')
            username = request.POST.get('username', 'postgres')
            password = request.POST.get('password', '')
            database_name = request.POST.get('database_name', 'crm')

            # إنشاء قاعدة بيانات
            try:
                # إنشاء جداول قاعدة البيانات
                from django.core.management import call_command
                call_command('migrate')

                # إنشاء إعداد قاعدة البيانات
                db_config = DatabaseConfig.objects.create(
                    name=_('قاعدة البيانات الرئيسية'),
                    db_type=db_type,
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    database_name=database_name,
                    is_active=True,
                    is_default=True
                )

                # إنشاء مستخدم مسؤول إذا لم يكن هناك مستخدمين
                if not has_users and request.POST.get('create_admin') == 'on':
                    admin_username = request.POST.get('admin_username', 'admin')
                    admin_email = request.POST.get('admin_email', 'admin@example.com')
                    admin_password = request.POST.get('admin_password', 'admin')

                    # إنشاء المستخدم المسؤول
                    create_superuser(admin_username, admin_email, admin_password)

                messages.success(request, _('تم إعداد النظام بنجاح! يمكنك الآن تسجيل الدخول.'))
                return redirect('accounts:login')
            except Exception as setup_error:
                messages.error(request, _('حدث خطأ أثناء إعداد النظام: {}').format(str(setup_error)))

        # عرض نموذج الإعداد البسيط
        return render(request, 'db_manager/setup.html', {
            'simple_setup': True,
            'has_users': has_users,
            'error': str(e)
        })


def setup_with_token(request, token):
    """صفحة الإعداد باستخدام رمز إعداد"""
    # التحقق من صحة الرمز
    token_obj = get_object_or_404(SetupToken, token=token)

    if not token_obj.is_valid:
        messages.error(request, _('رمز الإعداد غير صالح أو منتهي الصلاحية.'))
        return redirect('accounts:login')

    # التحقق من وجود مستخدمين في النظام
    from django.contrib.auth.models import User
    if User.objects.count() > 0:
        # إذا كان هناك مستخدمين بالفعل، نتحقق مما إذا كان المستخدم الحالي مسؤولًا
        if request.user.is_authenticated and request.user.is_superuser:
            # المستخدم مسؤول، يمكنه متابعة الإعداد
            pass
        else:
            # هناك مستخدمين بالفعل ولكن المستخدم الحالي ليس مسؤولًا
            messages.error(request, _('لا يمكن استخدام صفحة الإعداد لأن النظام تم إعداده بالفعل. يرجى تسجيل الدخول كمسؤول.'))
            return redirect('accounts:login')

    # التحقق من وجود قاعدة بيانات نشطة
    existing_db = DatabaseConfig.objects.filter(is_active=True).first()

    if request.method == 'POST':
        form = DatabaseSetupForm(request.POST, request.FILES)
        if form.is_valid():
            # إنشاء إعداد قاعدة البيانات إذا لم يكن موجودًا بالفعل
            if not existing_db:
                db_config = DatabaseConfig(
                    name=_('قاعدة البيانات الرئيسية'),
                    db_type=form.cleaned_data['db_type'],
                    host=form.cleaned_data.get('host', ''),
                    port=form.cleaned_data.get('port', ''),
                    username=form.cleaned_data.get('username', ''),
                    password=form.cleaned_data.get('password', ''),
                    database_name=form.cleaned_data.get('database_name', ''),
                    is_active=True,
                    is_default=True
                )

                # معالجة ملف SQLite إذا تم تحميله
                if form.cleaned_data['db_type'] == 'sqlite' and form.cleaned_data.get('sqlite_file'):
                    sqlite_file = form.cleaned_data['sqlite_file']
                    file_path = default_storage.save(f'db_files/{sqlite_file.name}', ContentFile(sqlite_file.read()))
                    db_config.connection_string = f'sqlite:///{file_path}'

                # حفظ إعداد قاعدة البيانات
                db_config.save()
            else:
                # استخدام قاعدة البيانات الموجودة
                db_config = existing_db

            # إنشاء مستخدم مسؤول إذا تم اختيار ذلك ولم يكن هناك مستخدمين
            if form.cleaned_data.get('create_superuser') and User.objects.count() == 0:
                # استخدام أمر Django لإنشاء مستخدم مسؤول
                username = form.cleaned_data['admin_username']
                email = form.cleaned_data['admin_email']
                password = form.cleaned_data['admin_password']

                # إنشاء المستخدم المسؤول مباشرة
                success = create_superuser(username, email, password)

                if success:
                    messages.success(request, _('تم إنشاء المستخدم المسؤول بنجاح.'))
                else:
                    messages.error(request, _('حدث خطأ أثناء إنشاء المستخدم المسؤول.'))

            # تحديث رمز الإعداد
            token_obj.is_used = True
            token_obj.used_at = timezone.now()
            token_obj.save()

            messages.success(request, _('تم إعداد النظام بنجاح! يمكنك الآن تسجيل الدخول.'))
            return redirect('accounts:login')
    else:
        # إذا كانت هناك قاعدة بيانات موجودة، نملأ النموذج ببياناتها
        if existing_db:
            initial_data = {
                'db_type': existing_db.db_type,
                'host': existing_db.host,
                'port': existing_db.port,
                'username': existing_db.username,
                'database_name': existing_db.database_name,
                'create_superuser': User.objects.count() == 0,  # تفعيل إنشاء مستخدم مسؤول فقط إذا لم يكن هناك مستخدمين
            }
            form = DatabaseSetupForm(initial=initial_data)
        else:
            form = DatabaseSetupForm(initial={'create_superuser': True, 'db_type': 'postgresql'})

    return render(request, 'db_manager/setup_with_token.html', {
        'form': form,
        'token': token_obj,
        'existing_db': existing_db,
        'has_users': User.objects.count() > 0,
    })


def create_superuser(username, email, password):
    """إنشاء مستخدم مسؤول جديد"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # التحقق مما إذا كان المستخدم موجودًا بالفعل
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            return True
    except Exception as e:
        print(f"Error creating superuser: {e}")
        return False


@login_required
@user_passes_test(is_superuser)
def database_list(request):
    """عرض قائمة قواعد البيانات"""
    databases = DatabaseConfig.objects.all()

    # التحقق من وجود قاعدة بيانات افتراضية
    default_db = DatabaseConfig.objects.filter(is_default=True).first()

    # إذا لم توجد قاعدة بيانات افتراضية وتوجد قواعد بيانات نشطة، نقوم بتعيين أول قاعدة بيانات نشطة كافتراضية
    if not default_db:
        active_db = DatabaseConfig.objects.filter(is_active=True).first()
        if active_db:
            active_db.is_default = True
            active_db.save()
            messages.success(request, _('تم تعيين قاعدة البيانات "{}" كقاعدة بيانات افتراضية.').format(active_db.name))
            default_db = active_db

    return render(request, 'db_manager/database_list.html', {
        'databases': databases,
        'default_db': default_db,
    })


@login_required
@user_passes_test(is_superuser)
def database_create(request):
    """إنشاء إعداد قاعدة بيانات جديد"""
    if request.method == 'POST':
        form = DatabaseConfigForm(request.POST)
        if form.is_valid():
            db_config = form.save(commit=False)

            # التحقق من وجود قاعدة بيانات افتراضية
            default_db_exists = DatabaseConfig.objects.filter(is_default=True).exists()

            # إذا لم توجد قاعدة بيانات افتراضية، نقوم بتعيين هذه القاعدة كافتراضية
            if not default_db_exists:
                db_config.is_default = True

            # حفظ إعداد قاعدة البيانات
            db_config.save()

            if db_config.is_default:
                messages.success(request, _('تم إنشاء إعداد قاعدة البيانات بنجاح وتعيينه كقاعدة بيانات افتراضية.'))
            else:
                messages.success(request, _('تم إنشاء إعداد قاعدة البيانات بنجاح.'))

            return redirect('db_manager:database_list')
    else:
        form = DatabaseConfigForm()

    return render(request, 'db_manager/database_form.html', {
        'form': form,
        'title': _('إنشاء إعداد قاعدة بيانات جديد'),
    })


@login_required
@user_passes_test(is_superuser)
def database_edit(request, pk):
    """تعديل إعداد قاعدة بيانات"""
    db_config = get_object_or_404(DatabaseConfig, pk=pk)

    if request.method == 'POST':
        form = DatabaseConfigForm(request.POST, instance=db_config)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث إعداد قاعدة البيانات بنجاح.'))
            return redirect('db_manager:database_list')
    else:
        form = DatabaseConfigForm(instance=db_config)

    return render(request, 'db_manager/database_form.html', {
        'form': form,
        'db_config': db_config,
        'title': _('تعديل إعداد قاعدة البيانات'),
    })


@login_required
@user_passes_test(is_superuser)
def database_delete(request, pk):
    """حذف إعداد قاعدة بيانات"""
    db_config = get_object_or_404(DatabaseConfig, pk=pk)

    if request.method == 'POST':
        # لا يمكن حذف قاعدة البيانات الافتراضية
        if db_config.is_default:
            messages.error(request, _('لا يمكن حذف قاعدة البيانات الافتراضية.'))
            return redirect('db_manager:database_list')

        db_config.delete()
        messages.success(request, _('تم حذف إعداد قاعدة البيانات بنجاح.'))
        return redirect('db_manager:database_list')

    return render(request, 'db_manager/database_confirm_delete.html', {
        'db_config': db_config,
    })


@login_required
@user_passes_test(is_superuser)
def database_set_default(request, pk):
    """تعيين قاعدة بيانات كافتراضية"""
    db_config = get_object_or_404(DatabaseConfig, pk=pk)

    if request.method == 'POST':
        # إلغاء تعيين جميع قواعد البيانات الأخرى كافتراضية
        DatabaseConfig.objects.exclude(pk=pk).update(is_default=False)

        # تعيين قاعدة البيانات الحالية كافتراضية
        db_config.is_default = True
        db_config.save()

        messages.success(request, _('تم تعيين قاعدة البيانات كافتراضية بنجاح.'))

    return redirect('db_manager:database_list')


@login_required
@user_passes_test(is_superuser)
def database_test_connection(request, pk):
    """اختبار الاتصال بقاعدة البيانات"""
    db_config = get_object_or_404(DatabaseConfig, pk=pk)

    success = False
    message = ""

    try:
        if db_config.db_type == 'postgresql':
            # اختبار اتصال PostgreSQL
            conn = psycopg2.connect(
                host=db_config.host,
                port=db_config.port or '5432',
                database=db_config.database_name,
                user=db_config.username,
                password=db_config.password
            )
            conn.close()
            success = True
            message = _('تم الاتصال بقاعدة البيانات بنجاح.')
        elif db_config.db_type == 'sqlite':
            # اختبار اتصال SQLite
            if db_config.connection_string:
                # استخراج مسار الملف من سلسلة الاتصال
                file_path = db_config.connection_string.replace('sqlite:///', '')
                conn = sqlite3.connect(file_path)
                conn.close()
                success = True
                message = _('تم الاتصال بقاعدة البيانات بنجاح.')
            else:
                success = False
                message = _('سلسلة الاتصال غير صالحة.')
        else:
            success = False
            message = _('نوع قاعدة البيانات غير مدعوم للاختبار التلقائي.')
    except Exception as e:
        success = False
        message = str(e)

    return JsonResponse({
        'success': success,
        'message': message,
    })


@login_required
@user_passes_test(is_superuser)
def backup_list(request):
    """عرض قائمة النسخ الاحتياطية"""
    backups = DatabaseBackup.objects.all()
    databases = DatabaseConfig.objects.filter(is_active=True)
    default_db = DatabaseConfig.objects.filter(is_default=True).first()

    # تنظيف سجلات الاستيراد القديمة
    cleanup_old_imports()

    return render(request, 'db_manager/backup_list.html', {
        'backups': backups,
        'databases': databases,
        'default_db': default_db,
    })


@login_required
@user_passes_test(is_superuser)
def backup_create(request):
    """إنشاء نسخة احتياطية جديدة"""
    databases = DatabaseConfig.objects.filter(is_active=True)
    default_db = DatabaseConfig.objects.filter(is_default=True).first()

    if request.method == 'POST':
        form = DatabaseBackupForm(request.POST, user=request.user)
        if form.is_valid():
            backup = form.save(commit=False)

            # إنشاء النسخة الاحتياطية
            db_config = backup.database_config

            # إنشاء ملف مؤقت للنسخة الاحتياطية في مجلد النسخ الاحتياطية
            from django.conf import settings
            backup_dir = settings.BACKUP_ROOT
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if db_config.db_type == 'postgresql':
                suffix = '.dump'
            else:
                suffix = '.json'

            temp_filename = f"temp_backup_{timestamp}{suffix}"
            temp_path = os.path.join(backup_dir, temp_filename)

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
        'databases': databases,
        'default_db': default_db,
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
    try:
        backup = get_object_or_404(DatabaseBackup, pk=pk)

        if request.method == 'POST':
            # التحقق من وجود الملف
            if not backup.file:
                messages.error(request, _('ملف النسخة الاحتياطية غير موجود.'))
                return redirect('db_manager:backup_list')

            # تنظيف قاعدة البيانات من سجلات الاستيراد القديمة
            cleanup_old_imports()

            # حذف جميع عمليات الاستيراد السابقة
            try:
                # حذف جميع سجلات الاستيراد بشكل آمن
                DatabaseImport.objects.all().delete()

                # إعادة ضبط تسلسل المعرفات في قاعدة البيانات
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT setval('db_manager_databaseimport_id_seq', 1, false);")
            except Exception as e:
                # تسجيل الخطأ ولكن متابعة العملية
                print(f"Error resetting database sequence: {e}")

            # إنشاء سجل استيراد جديد مع نسخة من الملف
            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage

            # إنشاء اسم ملف جديد مع طابع زمني
            import os
            from datetime import datetime
            file_name = os.path.basename(backup.file.name)
            file_ext = os.path.splitext(file_name)[1]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_file_name = f"import_{timestamp}{file_ext}"

            try:
                # إنشاء نسخة من الملف
                with backup.file.open('rb') as f:
                    file_content = f.read()

                # إنشاء سجل استيراد جديد بدون حفظه
                db_import = DatabaseImport()

                # تعيين الحقول
                db_import.database_config = backup.database_config
                db_import.status = 'pending'  # استخدام حالة "قيد الانتظار" بدلاً من "قيد التنفيذ"
                db_import.created_by = request.user

                # حفظ السجل أولاً لإنشاء المعرف
                db_import.save()

                # ثم حفظ الملف
                db_import.file.save(new_file_name, ContentFile(file_content), save=True)

                # تحديث الحالة إلى "قيد التنفيذ"
                db_import.status = 'in_progress'
                db_import.save()

                # بدء عملية الاستيراد في خلفية منفصلة
                thread = threading.Thread(
                    target=process_import,
                    args=(db_import.id,)
                )
                thread.daemon = True  # جعل الخيط daemon لإنهائه عند إنهاء البرنامج الرئيسي
                thread.start()

                messages.success(request, _('بدأت عملية استعادة النسخة الاحتياطية. يمكنك متابعة التقدم في صفحة الاستيراد.'))
                return redirect('db_manager:import_status', pk=db_import.id)
            except Exception as e:
                # في حالة حدوث خطأ، عرض رسالة خطأ وتسجيل الخطأ
                messages.error(request, _('حدث خطأ أثناء إنشاء عملية الاستيراد: {}').format(str(e)))
                import traceback
                traceback.print_exc()
                return redirect('db_manager:backup_list')

        return render(request, 'db_manager/backup_confirm_restore.html', {
            'backup': backup,
        })
    except Exception as e:
        # في حالة حدوث خطأ غير متوقع، عرض رسالة خطأ وتسجيل الخطأ
        messages.error(request, _('حدث خطأ غير متوقع: {}').format(str(e)))
        import traceback
        traceback.print_exc()
        return redirect('db_manager:backup_list')


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
    try:
        # تنظيف قاعدة البيانات من سجلات الاستيراد القديمة
        cleanup_old_imports()

        # إعادة ضبط تسلسل المعرفات في قاعدة البيانات
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT setval('db_manager_databaseimport_id_seq', 1, false);")
        except Exception as e:
            # تسجيل الخطأ ولكن متابعة العملية
            print(f"Error resetting database sequence: {e}")

        databases = DatabaseConfig.objects.filter(is_active=True)
        default_db = DatabaseConfig.objects.filter(is_default=True).first()

        if request.method == 'POST':
            form = DatabaseImportForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                try:
                    # إنشاء سجل استيراد جديد بدون حفظه مباشرة
                    db_import = form.save(commit=False)

                    # تعيين الحالة والمستخدم
                    db_import.status = 'pending'  # استخدام حالة "قيد الانتظار" بدلاً من "قيد التنفيذ"
                    db_import.created_by = request.user

                    # حفظ السجل
                    db_import.save()

                    # تحديث الحالة إلى "قيد التنفيذ"
                    db_import.status = 'in_progress'
                    db_import.save()

                    # بدء عملية الاستيراد في خلفية منفصلة
                    thread = threading.Thread(
                        target=process_import,
                        args=(db_import.id,)
                    )
                    thread.daemon = True  # جعل الخيط daemon لإنهائه عند إنهاء البرنامج الرئيسي
                    thread.start()

                    messages.success(request, _('بدأت عملية الاستيراد. يمكنك متابعة التقدم في صفحة الحالة.'))
                    return redirect('db_manager:import_status', pk=db_import.id)
                except Exception as e:
                    # في حالة حدوث خطأ، عرض رسالة خطأ وتسجيل الخطأ
                    messages.error(request, _('حدث خطأ أثناء إنشاء عملية الاستيراد: {}').format(str(e)))
                    import traceback
                    traceback.print_exc()
            else:
                # في حالة عدم صحة النموذج، عرض رسالة خطأ
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            form = DatabaseImportForm(user=request.user)

        return render(request, 'db_manager/import_form.html', {
            'form': form,
            'databases': databases,
            'default_db': default_db,
        })
    except Exception as e:
        # في حالة حدوث خطأ غير متوقع، عرض رسالة خطأ وتسجيل الخطأ
        messages.error(request, _('حدث خطأ غير متوقع: {}').format(str(e)))
        import traceback
        traceback.print_exc()
        return redirect('db_manager:database_list')


def process_import(import_id):
    """معالجة عملية استيراد قاعدة البيانات"""
    try:
        db_import = DatabaseImport.objects.get(id=import_id)
    except DatabaseImport.DoesNotExist:
        print(f"Error: Import with ID {import_id} does not exist")
        return

    try:
        # تحديث الحالة
        db_import.status = 'in_progress'
        db_import.log = "بدء عملية الاستيراد...\n"
        db_import.save()

        # الحصول على مسار الملف
        file_path = db_import.file.path

        # تحديد نوع الملف
        is_json = file_path.lower().endswith('.json')
        is_dump = file_path.lower().endswith('.dump')

        # تحديث السجل
        db_import.log += f"نوع الملف: {'JSON' if is_json else 'PostgreSQL Dump'}\n"
        db_import.log += f"مسار الملف: {file_path}\n"
        db_import.log += "جاري التحضير لعملية الاستيراد...\n"
        db_import.save()

        # استيراد البيانات
        if is_json:
            # تحديث السجل
            db_import.log += "بدء استيراد ملف JSON باستخدام Django loaddata...\n"
            db_import.save()

            # استخدام أمر Django loaddata
            output = io.StringIO()
            call_command(
                'loaddata',
                file_path,
                stdout=output
            )

            # تحديث السجل
            db_import.log += "تم استيراد ملف JSON بنجاح.\n"
            db_import.log += "نتيجة العملية:\n"
            db_import.log += output.getvalue()
            db_import.save()
        elif is_dump:
            # تحديث السجل
            db_import.log += "بدء استيراد ملف PostgreSQL Dump...\n"
            db_import.save()

            # استخدام أمر pg_restore
            db_config = db_import.database_config

            # تعيين متغيرات البيئة للاتصال بقاعدة البيانات
            os.environ['PGHOST'] = db_config.host
            os.environ['PGPORT'] = db_config.port or '5432'
            os.environ['PGDATABASE'] = db_config.database_name
            os.environ['PGUSER'] = db_config.username
            os.environ['PGPASSWORD'] = db_config.password

            # تحديث السجل
            db_import.log += f"الاتصال بقاعدة البيانات: {db_config.database_name} على {db_config.host}:{db_config.port or '5432'}\n"
            db_import.save()

            # محاولة استخدام pg_restore
            try:
                # التحقق من وجود أداة pg_restore
                try:
                    # محاولة تحديد موقع pg_restore
                    pg_restore_path = 'pg_restore'
                    subprocess.check_output([pg_restore_path, '--version'], stderr=subprocess.STDOUT, text=True)

                    # تنفيذ أمر pg_restore مع تحسينات الأداء
                    cmd = [
                        pg_restore_path,
                        '--dbname=' + db_config.database_name,
                        '--clean',
                        '--if-exists',
                        '--jobs=4',  # استخدام 4 مهام متوازية لتسريع العملية
                        '--no-owner',  # تجاهل معلومات المالك
                        '--no-privileges',  # تجاهل الصلاحيات
                        file_path
                    ]

                    # تحديث السجل
                    db_import.log += f"تنفيذ الأمر: {' '.join(cmd)}\n"
                    db_import.save()

                    # تنفيذ الأمر مع تحديث السجل بشكل دوري
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    # pg_restore غير موجود، محاولة استخدام psql
                    db_import.log += f"أداة pg_restore غير متوفرة: {str(e)}\nمحاولة استخدام psql...\n"
                    db_import.save()

                    try:
                        # محاولة تحديد موقع psql
                        psql_path = 'psql'
                        subprocess.check_output([psql_path, '--version'], stderr=subprocess.STDOUT, text=True)

                        # إنشاء ملف SQL مؤقت من ملف الـ dump
                        temp_sql_path = file_path + '.sql'
                        db_import.log += f"تحويل ملف الـ dump إلى SQL...\n"
                        db_import.save()

                        # استخدام psql لاستعادة النسخة الاحتياطية
                        cmd = [
                            psql_path,
                            '-h', db_config.host,
                            '-p', db_config.port or '5432',
                            '-U', db_config.username,
                            '-d', db_config.database_name,
                            '-f', file_path
                        ]

                        # تحديث السجل
                        db_import.log += f"تنفيذ الأمر: {' '.join(cmd)}\n"
                        db_import.save()

                        # تنفيذ الأمر مع تحديث السجل بشكل دوري
                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            bufsize=1,
                            universal_newlines=True
                        )
                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        # psql غير موجود أيضًا، استخدام طريقة بديلة
                        db_import.log += f"أداة psql غير متوفرة: {str(e)}\nاستخدام طريقة بديلة...\n"
                        db_import.save()

                        # التحقق من نوع الملف
                        if file_path.endswith('.json'):
                            # استخدام loaddata لاستعادة ملف JSON
                            db_import.log += "استخدام Django loaddata لاستعادة البيانات...\n"
                            db_import.save()

                            output = io.StringIO()
                            call_command('loaddata', file_path, stdout=output)

                            # تحديث السجل
                            db_import.log += "تم استيراد البيانات بنجاح باستخدام Django loaddata.\n"
                            db_import.log += "نتيجة العملية:\n"
                            db_import.log += output.getvalue()
                            db_import.save()

                            # تعيين الحالة إلى مكتملة
                            db_import.status = 'completed'
                            db_import.completed_at = timezone.now()
                            db_import.log += f"\nاكتملت العملية بنجاح في {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            db_import.save()
                            return
                        else:
                            # لا يمكن استعادة ملف dump بدون أدوات PostgreSQL
                            db_import.status = 'failed'
                            db_import.log += "فشل استعادة البيانات: لا يمكن استعادة ملف PostgreSQL dump بدون أدوات PostgreSQL.\n"
                            db_import.save()
                            return
            except Exception as e:
                # حدث خطأ أثناء محاولة استعادة البيانات
                db_import.status = 'failed'
                db_import.log += f"حدث خطأ أثناء محاولة استعادة البيانات: {str(e)}\n"
                db_import.save()
                return

            # قراءة المخرجات بشكل تدريجي
            stdout_lines = []
            stderr_lines = []

            # قراءة المخرجات القياسية
            for line in process.stdout:
                stdout_lines.append(line)
                # تحديث السجل كل 10 سطور
                if len(stdout_lines) % 10 == 0:
                    db_import.log += f"جاري الاستيراد... ({len(stdout_lines)} سطر)\n"
                    db_import.save()

            # قراءة مخرجات الأخطاء
            for line in process.stderr:
                stderr_lines.append(line)
                # تحديث السجل كل 10 سطور
                if len(stderr_lines) % 10 == 0:
                    db_import.log += f"ملاحظات: {line}\n"
                    db_import.save()

            # انتظار انتهاء العملية
            process.wait()

            # تحديث السجل بالنتيجة النهائية
            if process.returncode == 0:
                db_import.log += "تم استيراد ملف PostgreSQL Dump بنجاح.\n"
            else:
                db_import.log += f"انتهت العملية برمز الخروج: {process.returncode}\n"

            # إضافة المخرجات الكاملة إلى السجل
            if stdout_lines:
                db_import.log += "\nمخرجات العملية:\n"
                db_import.log += "".join(stdout_lines)

            if stderr_lines:
                db_import.log += "\nملاحظات وأخطاء:\n"
                db_import.log += "".join(stderr_lines)

            db_import.save()

        # تحديث الحالة
        db_import.status = 'completed'
        db_import.completed_at = timezone.now()
        db_import.log += f"\nاكتملت العملية بنجاح في {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        db_import.save()
    except Exception as e:
        # تحديث الحالة في حالة الفشل
        db_import.status = 'failed'
        db_import.log += f"\nفشلت العملية بسبب الخطأ التالي:\n{str(e)}\n"
        db_import.save()


@login_required
@user_passes_test(is_superuser)
def database_export(request):
    """تصدير قاعدة البيانات إلى ملف"""
    databases = DatabaseConfig.objects.filter(is_active=True)
    default_db = DatabaseConfig.objects.filter(is_default=True).first()

    if request.method == 'POST':
        db_config_id = request.POST.get('database_config')
        export_format = request.POST.get('format', 'json')

        if not db_config_id:
            messages.error(request, _('يرجى اختيار قاعدة بيانات.'))
            return redirect('db_manager:database_list')

        db_config = get_object_or_404(DatabaseConfig, pk=db_config_id)

        # إنشاء ملف مؤقت للتصدير في مجلد النسخ الاحتياطية
        from django.conf import settings
        backup_dir = settings.BACKUP_ROOT
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if export_format == 'json':
            suffix = '.json'
        else:
            suffix = '.dump'

        temp_filename = f"temp_export_{timestamp}{suffix}"
        temp_path = os.path.join(backup_dir, temp_filename)

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

    return render(request, 'db_manager/export_form.html', {
        'databases': databases,
        'default_db': default_db,
    })


@login_required
@user_passes_test(is_superuser)
def import_status(request, pk):
    """عرض حالة عملية الاستيراد"""
    try:
        db_import = get_object_or_404(DatabaseImport, pk=pk)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # استجابة AJAX لتحديث الحالة
            try:
                return JsonResponse({
                    'status': db_import.status,
                    'completed_at': db_import.completed_at.isoformat() if db_import.completed_at else None,
                    'log': db_import.log or '',
                })
            except Exception as e:
                # في حالة حدوث خطأ في استجابة AJAX
                return JsonResponse({
                    'status': 'error',
                    'error': str(e),
                })

        return render(request, 'db_manager/import_status.html', {
            'db_import': db_import,
        })
    except Exception as e:
        # في حالة حدوث خطأ غير متوقع
        messages.error(request, _('حدث خطأ أثناء عرض حالة الاستيراد: {}').format(str(e)))

        # تسجيل الخطأ
        import traceback
        traceback.print_exc()

        # إعادة توجيه المستخدم إلى صفحة قائمة النسخ الاحتياطية
        return redirect('db_manager:backup_list')


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


@login_required
@user_passes_test(is_superuser)
def import_data_from_file(request):
    """استيراد البيانات من ملف"""
    if request.method == 'POST':
        # التحقق من وجود الملف
        if 'import_file' not in request.FILES:
            messages.error(request, _('يرجى اختيار ملف للاستيراد.'))
            return redirect('db_manager:database_list')

        # الحصول على الملف
        import_file = request.FILES['import_file']

        # التحقق من نوع الملف
        is_json = import_file.name.lower().endswith('.json')
        is_dump = import_file.name.lower().endswith('.dump')

        if not (is_json or is_dump):
            messages.error(request, _('نوع الملف غير مدعوم. يجب أن يكون .json أو .dump'))
            return redirect('db_manager:database_list')

        # الحصول على قاعدة البيانات
        db_config_id = request.POST.get('db_config')
        if not db_config_id:
            messages.error(request, _('يرجى اختيار قاعدة بيانات.'))
            return redirect('db_manager:database_list')

        try:
            db_config = DatabaseConfig.objects.get(id=db_config_id)
        except DatabaseConfig.DoesNotExist:
            messages.error(request, _('قاعدة البيانات غير موجودة.'))
            return redirect('db_manager:database_list')

        # حفظ الملف مؤقتًا
        import os
        from django.conf import settings
        from datetime import datetime

        # إنشاء مجلد مؤقت إذا لم يكن موجودًا
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_imports')
        os.makedirs(temp_dir, exist_ok=True)

        # إنشاء اسم ملف فريد
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"temp_import_{timestamp}_{import_file.name}"
        file_path = os.path.join(temp_dir, file_name)

        # حفظ الملف
        with open(file_path, 'wb+') as destination:
            for chunk in import_file.chunks():
                destination.write(chunk)

        try:
            # استيراد البيانات
            if is_json:
                # استخدام أمر Django loaddata
                from django.core.management import call_command
                call_command('loaddata', file_path)
                messages.success(request, _('تم استيراد البيانات بنجاح.'))
            elif is_dump and db_config.db_type == 'postgresql':
                # تعيين متغيرات البيئة للاتصال بقاعدة البيانات
                os.environ['PGHOST'] = db_config.host
                os.environ['PGPORT'] = db_config.port or '5432'
                os.environ['PGDATABASE'] = db_config.database_name
                os.environ['PGUSER'] = db_config.username
                os.environ['PGPASSWORD'] = db_config.password

                # محاولة استخدام pg_restore
                import subprocess
                try:
                    # التحقق من وجود أداة pg_restore
                    try:
                        # محاولة تحديد موقع pg_restore
                        pg_restore_path = 'pg_restore'
                        subprocess.check_output([pg_restore_path, '--version'], stderr=subprocess.STDOUT, text=True)

                        # تنفيذ أمر pg_restore
                        cmd = [
                            pg_restore_path,
                            '--dbname=' + db_config.database_name,
                            '--clean',
                            '--if-exists',
                            '--jobs=4',  # استخدام 4 مهام متوازية لتسريع العملية
                            '--no-owner',  # تجاهل معلومات المالك
                            '--no-privileges',  # تجاهل الصلاحيات
                            file_path
                        ]
                        result = subprocess.run(cmd, capture_output=True, text=True)

                        if result.returncode == 0:
                            messages.success(request, _('تم استيراد البيانات بنجاح.'))
                        else:
                            messages.warning(request, _('تم استيراد البيانات مع بعض التحذيرات.'))
                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        # pg_restore غير موجود، محاولة استخدام psql
                        try:
                            # محاولة تحديد موقع psql
                            psql_path = 'psql'
                            subprocess.check_output([psql_path, '--version'], stderr=subprocess.STDOUT, text=True)

                            # استخدام psql لاستعادة النسخة الاحتياطية
                            cmd = [
                                psql_path,
                                '-h', db_config.host,
                                '-p', db_config.port or '5432',
                                '-U', db_config.username,
                                '-d', db_config.database_name,
                                '-f', file_path
                            ]
                            result = subprocess.run(cmd, capture_output=True, text=True)

                            if result.returncode == 0:
                                messages.success(request, _('تم استيراد البيانات بنجاح باستخدام psql.'))
                            else:
                                messages.warning(request, _('تم استيراد البيانات مع بعض التحذيرات.'))
                        except (subprocess.CalledProcessError, FileNotFoundError) as e:
                            # psql غير موجود أيضًا، عرض رسالة خطأ
                            messages.error(request, _('أدوات PostgreSQL غير متوفرة على الخادم. لا يمكن استيراد ملف PostgreSQL dump.'))
                except Exception as e:
                    messages.error(request, _('حدث خطأ أثناء استيراد البيانات: {}').format(str(e)))
            else:
                messages.error(request, _('نوع قاعدة البيانات غير مدعوم للاستيراد.'))
        except Exception as e:
            messages.error(request, _('حدث خطأ أثناء استيراد البيانات: {}').format(str(e)))
        finally:
            # حذف الملف المؤقت
            if os.path.exists(file_path):
                os.unlink(file_path)

    return redirect('db_manager:database_list')
