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
            return redirect('data_management:db_manager:database_detail', pk=database.pk)
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
            return redirect('data_management:db_manager:database_detail', pk=database.pk)
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
        return redirect('data_management:db_manager:database_list')

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
        return redirect('data_management:db_manager:database_list')

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
        return redirect('data_management:db_manager:database_list')

    context = {
        'database': database,
        'title': _('تعيين قاعدة البيانات كافتراضية'),
    }

    return render(request, 'data_management/db_manager/database_set_default.html', context)
