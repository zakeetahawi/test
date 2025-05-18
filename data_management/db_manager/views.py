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


def cleanup_old_imports(delete_all=False):
    """تنظيف سجلات الاستيراد القديمة"""
    from datetime import timedelta
    from django.utils import timezone
    from django.db import connection

    try:
        if delete_all:
            # حذف جميع سجلات الاستيراد
            imports = DatabaseImport.objects.all()

            # حذف الملفات أولاً ثم السجلات
            for import_record in imports:
                try:
                    if import_record.file:
                        import_record.file.delete(save=False)
                except Exception as e:
                    print(f"Error deleting import file: {e}")

            # حذف جميع السجلات
            imports.delete()

            # إعادة ضبط تسلسل المعرفات
            try:
                with connection.cursor() as cursor:
                    cursor.execute("ALTER SEQUENCE db_manager_databaseimport_id_seq RESTART WITH 1;")
            except Exception as e:
                print(f"Error resetting sequence after deleting all imports: {e}")

            print("All import records have been deleted and sequence reset.")
            return

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


def test_current_database_connection(request):
    """اختبار الاتصال بقاعدة البيانات الحالية"""
    success = False
    message = ""
    db_info = {}

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
        from django.db import connections
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
        # التحقق مما إذا كان المستخدم قد طلب حذف جميع سجلات الاستيراد
        reset_imports = request.GET.get('reset_imports', 'false').lower() == 'true'

        if reset_imports:
            # حذف جميع سجلات الاستيراد وإعادة ضبط التسلسل
            cleanup_old_imports(delete_all=True)
            messages.success(request, _('تم حذف جميع سجلات الاستيراد وإعادة ضبط التسلسل بنجاح.'))
            return redirect('db_manager:database_import')

        # تنظيف قاعدة البيانات من سجلات الاستيراد القديمة
        cleanup_old_imports()

        databases = DatabaseConfig.objects.filter(is_active=True)
        default_db = DatabaseConfig.objects.filter(is_default=True).first()

        if request.method == 'POST':
            # طباعة معلومات الطلب للتشخيص
            print("POST data:", request.POST)
            print("FILES data:", request.FILES)

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
                print("Form errors:", form.errors)
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
        db_import.log = "🚀 بدء عملية استيراد قاعدة البيانات...\n"
        db_import.log += f"⏱️ وقت البدء: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        db_import.log += f"📁 اسم الملف: {os.path.basename(db_import.file.name)}\n"
        db_import.log += f"💾 قاعدة البيانات: {db_import.database_config.name}\n"
        db_import.log += f"🔄 حذف البيانات القديمة: {'نعم' if db_import.clear_data else 'لا'}\n\n"
        db_import.save()

        # إنشاء نسخة احتياطية قبل الاستيراد
        db_import.log += "📦 إنشاء نسخة احتياطية قبل الاستيراد...\n"
        db_import.save()

        try:
            # إنشاء نسخة احتياطية
            from django.conf import settings
            from io import StringIO

            # التأكد من وجود مجلد النسخ الاحتياطية
            backup_dir = getattr(settings, 'BACKUP_ROOT', os.path.join(settings.MEDIA_ROOT, 'db_backups'))
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"pre_import_backup_{timestamp}.json"
            backup_path = os.path.join(backup_dir, backup_filename)

            # استخدام أمر Django dumpdata
            output = StringIO()
            from django.core.management import call_command

            call_command(
                'dumpdata',
                '--exclude', 'auth.permission',
                '--exclude', 'contenttypes',
                '--exclude', 'sessions',
                '--indent', '2',
                stdout=output
            )

            # حفظ النسخة الاحتياطية
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(output.getvalue())

            db_import.log += f"تم إنشاء نسخة احتياطية بنجاح: {backup_filename}\n"
            db_import.save()
        except Exception as e:
            db_import.log += f"تحذير: فشل إنشاء نسخة احتياطية: {str(e)}\n"
            db_import.log += "متابعة عملية الاستيراد...\n"
            db_import.save()

        # الحصول على مسار الملف
        file_path = db_import.file.path

        # تحديد نوع الملف
        file_ext = os.path.splitext(file_path)[1].lower()
        is_json = file_ext == '.json'
        is_dump = file_ext == '.dump'
        is_sql = file_ext == '.sql'

        # تحديث السجل
        file_type_emoji = '📄'
        if is_json:
            file_type_emoji = '📋'
            file_type_name = 'JSON'
        elif is_dump:
            file_type_emoji = '💾'
            file_type_name = 'PostgreSQL Dump'
        elif is_sql:
            file_type_emoji = '📊'
            file_type_name = 'SQL'
        else:
            file_type_name = 'غير معروف'

        db_import.log += f"{file_type_emoji} نوع الملف: {file_type_name}\n"
        db_import.log += f"📂 مسار الملف: {file_path}\n"

        # حجم الملف
        try:
            file_size = os.path.getsize(file_path)
            if file_size < 1024:
                file_size_str = f"{file_size} بايت"
            elif file_size < 1024 * 1024:
                file_size_str = f"{file_size / 1024:.2f} كيلوبايت"
            else:
                file_size_str = f"{file_size / (1024 * 1024):.2f} ميجابايت"
            db_import.log += f"📏 حجم الملف: {file_size_str}\n"
        except:
            pass

        db_import.log += "\n🔄 جاري التحضير لعملية الاستيراد...\n"
        db_import.save()

        # التحقق مما إذا كان المستخدم قد اختار حذف البيانات القديمة
        if db_import.clear_data:
            db_import.log += "تم تفعيل خيار حذف البيانات القديمة. جاري حذف البيانات الموجودة...\n"
            db_import.save()

            try:
                # حذف البيانات من جميع التطبيقات باستثناء auth وcontenttypes وsessions وaccounts
                from django.apps import apps
                from django.db import connection

                # الحصول على قائمة بجميع النماذج
                all_models = apps.get_models()

                # استبعاد النماذج من التطبيقات المحددة
                excluded_apps = ['auth', 'contenttypes', 'sessions', 'admin', 'accounts']
                # استبعاد نماذج إضافية حساسة
                excluded_models = ['accounts.user', 'accounts.userprofile', 'accounts.role', 'accounts.userrole', 'accounts.department', 'db_manager.databaseconfig']

                # تحضير قائمة النماذج للحذف
                models_to_clear = []
                for model in all_models:
                    model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                    # استبعاد النماذج من التطبيقات المستثناة أو النماذج المستثناة بالاسم
                    if model._meta.app_label not in excluded_apps and model_name not in excluded_models:
                        models_to_clear.append(model)

                db_import.log += f"سيتم حذف البيانات من {len(models_to_clear)} نموذج.\n"
                db_import.log += "ملاحظة: لن يتم حذف بيانات المستخدمين والأدوار وإعدادات قواعد البيانات.\n"
                db_import.save()

                # حذف البيانات من كل نموذج
                for model in models_to_clear:
                    model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                    db_import.log += f"حذف البيانات من {model_name}...\n"
                    db_import.save()

                    try:
                        # استخدام delete بدلاً من truncate لتجنب مشاكل CASCADE
                        model.objects.all().delete()

                        db_import.log += f"تم حذف البيانات من {model_name} بنجاح.\n"
                    except Exception as e:
                        db_import.log += f"تحذير: فشل حذف البيانات من {model_name}: {str(e)}\n"

                db_import.log += "تم حذف البيانات القديمة بنجاح.\n"
            except Exception as e:
                db_import.log += f"تحذير: فشل حذف البيانات القديمة: {str(e)}\n"
                db_import.log += "متابعة عملية الاستيراد...\n"

            db_import.save()

        # استيراد البيانات
        if is_json:
            # تحديث السجل
            db_import.log += "بدء استيراد ملف JSON باستخدام Django loaddata...\n"
            db_import.save()

            try:
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
            except Exception as e:
                db_import.status = 'failed'
                db_import.log += f"فشل استعادة البيانات باستخدام Django loaddata: {str(e)}\n"
                db_import.save()
                return
        elif is_dump:
            # تحديث السجل
            db_import.log += "بدء استيراد ملف DUMP...\n"
            db_import.log += "ملاحظة: استيراد ملفات DUMP على منصة Railway يتطلب استخدام طريقة بديلة.\n"
            db_import.save()

            # استيراد المكتبات اللازمة في بداية الوظيفة
            from django.conf import settings
            import tempfile
            from django.db import connection
            import json
            from django.core.management import call_command
            from io import StringIO

            try:
                # الحصول على معلومات الاتصال بقاعدة البيانات
                db_config = db_import.database_config

                # إنشاء مجلد مؤقت إذا لم يكن موجودًا
                temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
                os.makedirs(temp_dir, exist_ok=True)

                # إنشاء ملف مؤقت للتحويل
                temp_json_path = os.path.join(temp_dir, f"temp_import_{db_import.id}.json")

                db_import.log += "محاولة استيراد ملف DUMP...\n"
                db_import.save()

                # محاولة قراءة الملف بترميزات مختلفة
                encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'binary']
                file_content = None

                for encoding in encodings_to_try:
                    try:
                        if encoding == 'binary':
                            # قراءة الملف كملف ثنائي
                            with open(file_path, 'rb') as f:
                                file_content = f.read()
                            db_import.log += "تم قراءة الملف بنجاح كملف ثنائي.\n"
                            break
                        else:
                            # محاولة قراءة الملف بالترميز المحدد
                            with open(file_path, 'r', encoding=encoding) as f:
                                file_content = f.read()
                            db_import.log += f"تم قراءة الملف بنجاح باستخدام ترميز {encoding}.\n"
                            break
                    except UnicodeDecodeError:
                        db_import.log += f"فشل قراءة الملف باستخدام ترميز {encoding}. جاري تجربة ترميز آخر...\n"
                        continue

                if file_content is None:
                    db_import.status = 'failed'
                    db_import.log += "فشل قراءة الملف بجميع الترميزات المتاحة.\n"
                    db_import.save()
                    return

                # محاولة معالجة الملف كملف JSON
                try:
                    # التحقق مما إذا كان الملف يحتوي على بيانات JSON
                    if isinstance(file_content, bytes):
                        # تحويل البيانات الثنائية إلى نص
                        try:
                            text_content = file_content.decode('utf-8', errors='ignore')
                        except:
                            text_content = str(file_content)
                    else:
                        text_content = file_content

                    # البحث عن بيانات JSON في الملف
                    json_start = text_content.find('[{')
                    json_end = text_content.rfind('}]')

                    if json_start >= 0 and json_end > json_start:
                        # استخراج بيانات JSON من الملف
                        json_content = text_content[json_start:json_end+2]

                        # محاولة تحليل بيانات JSON
                        try:
                            data = json.loads(json_content)
                            db_import.log += "تم العثور على بيانات JSON في الملف وتحليلها بنجاح.\n"

                            # حفظ البيانات في ملف JSON مؤقت
                            with open(temp_json_path, 'w', encoding='utf-8') as json_file:
                                json.dump(data, json_file, ensure_ascii=False, indent=2)

                            # استخدام أمر Django loaddata
                            output = StringIO()
                            call_command(
                                'loaddata',
                                temp_json_path,
                                stdout=output
                            )

                            # تنظيف الملفات المؤقتة
                            try:
                                os.remove(temp_json_path)
                            except:
                                pass

                            db_import.log += "تم استيراد البيانات بنجاح.\n"
                            db_import.log += "نتيجة العملية:\n"
                            db_import.log += output.getvalue()
                            db_import.save()
                            return
                        except json.JSONDecodeError as json_error:
                            db_import.log += f"فشل تحليل بيانات JSON: {str(json_error)}\n"
                    else:
                        db_import.log += "لم يتم العثور على بيانات JSON في الملف.\n"
                except Exception as json_error:
                    db_import.log += f"فشل معالجة الملف كملف JSON: {str(json_error)}\n"

                # محاولة معالجة الملف كملف SQL
                db_import.log += "محاولة معالجة الملف كملف SQL...\n"

                try:
                    # إذا كان الملف ثنائيًا، نحاول تحويله إلى نص
                    if isinstance(file_content, bytes):
                        sql_content = file_content.decode('utf-8', errors='ignore')
                    else:
                        sql_content = file_content

                    # تنظيف محتوى SQL
                    sql_content = sql_content.replace('\x00', '')

                    # تقسيم الأوامر SQL
                    sql_commands = sql_content.split(';')

                    # تنفيذ كل أمر SQL على حدة
                    with connection.cursor() as cursor:
                        executed_commands = 0
                        for command in sql_commands:
                            command = command.strip()
                            if command:
                                try:
                                    cursor.execute(command + ';')
                                    executed_commands += 1
                                except Exception as sql_error:
                                    db_import.log += f"تحذير: فشل تنفيذ أمر SQL: {str(sql_error)}\n"

                        db_import.log += f"تم تنفيذ {executed_commands} أمر SQL بنجاح.\n"

                    if executed_commands > 0:
                        db_import.log += "تم استيراد البيانات بنجاح باستخدام SQL.\n"
                        db_import.save()
                        return
                    else:
                        db_import.log += "لم يتم تنفيذ أي أوامر SQL بنجاح.\n"
                except Exception as sql_error:
                    db_import.log += f"فشل معالجة الملف كملف SQL: {str(sql_error)}\n"

                # محاولة تحويل الملف إلى JSON وتصديره
                db_import.log += "محاولة تحويل الملف إلى JSON...\n"

                try:
                    # إنشاء ملف JSON من البيانات المستخرجة
                    from django.core.serializers import serialize
                    from django.apps import apps

                    # الحصول على جميع النماذج
                    all_models = apps.get_models()

                    # إنشاء ملف JSON يحتوي على جميع البيانات
                    with open(temp_json_path, 'w', encoding='utf-8') as json_file:
                        json_file.write('[')
                        first_model = True

                        for model in all_models:
                            try:
                                # تجاهل النماذج الداخلية
                                if model._meta.app_label in ['auth', 'contenttypes', 'sessions', 'admin']:
                                    continue

                                # الحصول على بيانات النموذج
                                model_data = serialize('json', model.objects.all())

                                # إزالة الأقواس المربعة من بداية ونهاية البيانات
                                model_data = model_data.strip()
                                if model_data.startswith('['):
                                    model_data = model_data[1:]
                                if model_data.endswith(']'):
                                    model_data = model_data[:-1]

                                # إضافة البيانات إلى الملف
                                if model_data and model_data.strip():
                                    if not first_model:
                                        json_file.write(',')
                                    json_file.write(model_data)
                                    first_model = False
                            except Exception as model_error:
                                db_import.log += f"تحذير: فشل استخراج بيانات النموذج {model.__name__}: {str(model_error)}\n"

                        json_file.write(']')

                    db_import.log += "تم إنشاء ملف JSON بنجاح.\n"

                    # استيراد البيانات من ملف JSON
                    output = StringIO()
                    call_command(
                        'loaddata',
                        temp_json_path,
                        stdout=output
                    )

                    # تنظيف الملفات المؤقتة
                    try:
                        os.remove(temp_json_path)
                    except:
                        pass

                    db_import.log += "تم استيراد البيانات بنجاح.\n"
                    db_import.log += "نتيجة العملية:\n"
                    db_import.log += output.getvalue()
                    db_import.save()
                    return
                except Exception as convert_error:
                    db_import.log += f"فشل تحويل الملف إلى JSON: {str(convert_error)}\n"

                # إذا وصلنا إلى هنا، فقد فشلت جميع المحاولات
                db_import.status = 'failed'
                db_import.log += "فشل استيراد البيانات باستخدام جميع الطرق المتاحة.\n"
                db_import.log += "يرجى التأكد من أن الملف بتنسيق صحيح (JSON أو SQL أو DUMP) ومتوافق مع هيكل قاعدة البيانات.\n"
                db_import.save()
                return
            except Exception as e:
                db_import.status = 'failed'
                db_import.log += f"فشل استيراد البيانات: {str(e)}\n"
                db_import.save()
                return
        else:
            # لا يمكن استعادة ملف غير معروف
            db_import.status = 'failed'
            db_import.log += "فشل استعادة البيانات: نوع الملف غير مدعوم. يرجى استخدام ملف JSON أو DUMP.\n"
            db_import.save()
            return

        # التحقق من البيانات المكررة بعد الاستعادة
        db_import.log += "\nالتحقق من البيانات المكررة بعد الاستعادة...\n"
        db_import.save()

        try:
            # التحقق من المستخدمين المكررين
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # استخدام استعلام SQL مباشر للبحث عن المستخدمين المكررين
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT username, COUNT(*) as count
                FROM accounts_user
                GROUP BY username
                HAVING COUNT(*) > 1
                """)
                duplicate_users = cursor.fetchall()

            if duplicate_users:
                db_import.log += f"تحذير: تم العثور على {len(duplicate_users)} مستخدم مكرر.\n"

                # حذف المستخدمين المكررين
                db_import.log += "محاولة إصلاح المستخدمين المكررين...\n"

                with connection.cursor() as cursor:
                    # حذف المستخدمين المكررين
                    cursor.execute("""
                    DELETE FROM accounts_user
                    WHERE id IN (
                        SELECT id
                        FROM (
                            SELECT id,
                                   ROW_NUMBER() OVER (PARTITION BY username ORDER BY id) as row_num
                            FROM accounts_user
                        ) t
                        WHERE t.row_num > 1
                    )
                    """)

                    # الحصول على عدد الصفوف المتأثرة
                    affected_rows = cursor.rowcount

                    db_import.log += f"تم حذف {affected_rows} مستخدم مكرر.\n"
            else:
                db_import.log += "لم يتم العثور على مستخدمين مكررين.\n"

            # التحقق من جلسات المستخدمين المكررة
            from django.contrib.sessions.models import Session

            # استخدام استعلام SQL مباشر للبحث عن الجلسات المكررة
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT session_key, COUNT(*) as count
                FROM django_session
                GROUP BY session_key
                HAVING COUNT(*) > 1
                """)
                duplicate_sessions = cursor.fetchall()

            if duplicate_sessions:
                db_import.log += f"تحذير: تم العثور على {len(duplicate_sessions)} جلسة مكررة.\n"

                # حذف الجلسات المكررة
                db_import.log += "محاولة إصلاح الجلسات المكررة...\n"

                for session_key, count in duplicate_sessions:
                    sessions = Session.objects.filter(session_key=session_key).order_by('-expire_date')

                    # الاحتفاظ بأحدث جلسة وحذف البقية
                    if sessions.count() > 1:
                        primary_session = sessions.first()
                        duplicate_sessions_to_delete = sessions.exclude(id=primary_session.id)
                        duplicate_sessions_to_delete.delete()

                db_import.log += "تم إصلاح الجلسات المكررة.\n"
            else:
                db_import.log += "لم يتم العثور على جلسات مكررة.\n"
        except Exception as e:
            db_import.log += f"تحذير: فشل التحقق من البيانات المكررة: {str(e)}\n"

        # تحديث الحالة
        db_import.status = 'completed'
        db_import.completed_at = timezone.now()
        db_import.log += f"\nاكتملت العملية بنجاح في {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        db_import.save()
    except Exception as e:
        # تحديث الحالة في حالة الفشل
        db_import.status = 'failed'
        db_import.log += f"\n❌ فشلت العملية بسبب الخطأ التالي:\n{str(e)}\n"

        # إضافة تفاصيل الخطأ
        error_traceback = traceback.format_exc()
        db_import.log += "\n🔍 تفاصيل الخطأ:\n"
        db_import.log += "=" * 50 + "\n"
        db_import.log += error_traceback
        db_import.log += "=" * 50 + "\n\n"

        # إضافة اقتراحات للإصلاح
        db_import.log += "💡 اقتراحات للإصلاح:\n"

        if "duplicate key value violates unique constraint" in str(e):
            db_import.log += "- يبدو أن هناك بيانات مكررة. حاول تفعيل خيار 'حذف البيانات القديمة' قبل الاستيراد.\n"
        elif "permission denied" in str(e).lower():
            db_import.log += "- مشكلة في صلاحيات الوصول لقاعدة البيانات. تأكد من أن المستخدم لديه الصلاحيات المناسبة.\n"
        elif "no such file or directory" in str(e).lower():
            db_import.log += "- لم يتم العثور على الملف. تأكد من وجود الملف وصلاحيته.\n"
        elif "could not connect to server" in str(e).lower():
            db_import.log += "- تعذر الاتصال بالخادم. تأكد من تشغيل خدمة قاعدة البيانات وصحة بيانات الاتصال.\n"
        elif "invalid input syntax" in str(e).lower():
            db_import.log += "- بنية البيانات غير صالحة. تأكد من تنسيق الملف وتوافقه مع هيكل قاعدة البيانات.\n"
        else:
            db_import.log += "- حاول التحقق من تنسيق الملف وتوافقه مع هيكل قاعدة البيانات.\n"
            db_import.log += "- تأكد من أن لديك صلاحيات كافية للوصول إلى قاعدة البيانات.\n"
            db_import.log += "- تحقق من اتصال قاعدة البيانات وتأكد من أنها تعمل بشكل صحيح.\n"

        db_import.log += "\n⏱️ وقت الفشل: " + timezone.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"
        db_import.completed_at = timezone.now()
        db_import.save()

        # تسجيل الخطأ في السجل
        print(f"Error during import: {str(e)}")
        traceback.print_exc()


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
                # استخدام Django dumpdata لإنشاء ملف JSON
                # ثم تحويله إلى تنسيق DUMP متوافق مع Railway

                # استخدام أمر Django dumpdata
                call_command(
                    'dumpdata',
                    '--exclude', 'auth.permission',
                    '--exclude', 'contenttypes',
                    '--indent', '2',
                    '--output', temp_path + '.json'
                )

                # إنشاء ملف DUMP متوافق مع Railway
                with open(temp_path + '.json', 'r', encoding='utf-8') as json_file:
                    json_data = json.load(json_file)

                # إنشاء ملف DUMP بتنسيق خاص
                with open(temp_path, 'w', encoding='utf-8') as dump_file:
                    dump_file.write("-- Railway Compatible PostgreSQL Dump\n")
                    dump_file.write("-- Generated by Django CRM System\n")
                    dump_file.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    # إضافة معلومات قاعدة البيانات
                    dump_file.write(f"-- Database: {db_config.database_name}\n")
                    dump_file.write("-- Format: Custom Railway Compatible\n\n")

                    # إضافة البيانات بتنسيق JSON
                    dump_file.write("-- JSON Data Begin\n")
                    json.dump(json_data, dump_file, ensure_ascii=False, indent=2)
                    dump_file.write("\n-- JSON Data End\n")

                # حذف الملف المؤقت
                os.unlink(temp_path + '.json')

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

        # إعادة توجيه المستخدم إلى صفحة قائمة النسخ الاحتياطية
        return redirect('data_management:db_dashboard')


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
def direct_import_form(request):
    """عرض نموذج الاستيراد المباشر"""
    databases = DatabaseConfig.objects.filter(is_active=True)
    default_db = DatabaseConfig.objects.filter(is_default=True).first()

    return render(request, 'db_manager/direct_import_form.html', {
        'databases': databases,
        'default_db': default_db,
    })


@login_required
@user_passes_test(is_superuser)
def import_data_from_file(request):
    """استيراد البيانات من ملف"""
    if request.method == 'POST':
        # طباعة معلومات الطلب للتشخيص
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)

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
            # استيراد البيانات - استخدام Django loaddata فقط
            if is_json:
                try:
                    # استخدام أمر Django loaddata
                    from django.core.management import call_command
                    call_command('loaddata', file_path)
                    messages.success(request, _('تم استيراد البيانات بنجاح.'))
                except Exception as e:
                    messages.error(request, _('حدث خطأ أثناء استيراد البيانات: {}').format(str(e)))
            else:
                messages.error(request, _('نوع الملف غير مدعوم. يرجى استخدام ملف JSON بدلاً من ذلك.'))
        except Exception as e:
            messages.error(request, _('حدث خطأ أثناء استيراد البيانات: {}').format(str(e)))
        finally:
            # حذف الملف المؤقت
            if os.path.exists(file_path):
                os.unlink(file_path)

    return redirect('db_manager:database_list')
