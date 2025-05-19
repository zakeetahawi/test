#!/usr/bin/env python
"""
سكريبت ما بعد النشر - يتم تنفيذه تلقائيًا بعد نشر التطبيق
يقوم بإنشاء الأقسام الافتراضية إذا لم تكن موجودة
"""

import os
import sys
import django
import time

# إضافة المسار الحالي إلى مسار النظام
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from data_management.railway_db_setup import setup_railway_database

def check_database_connection():
    """
    التحقق من اتصال قاعدة البيانات
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception as e:
        print(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return False

def main():
    """
    الوظيفة الرئيسية للسكريبت
    """
    print("بدء تنفيذ سكريبت ما بعد النشر...")

    # إعداد قاعدة بيانات Railway تلقائياً
    print("جاري إعداد قاعدة بيانات Railway...")
    try:
        setup_railway_database()
        print("تم إعداد قاعدة بيانات Railway بنجاح.")
    except Exception as e:
        print(f"خطأ في إعداد قاعدة بيانات Railway: {e}")

    # تنفيذ الترحيلات مرة أخرى للتأكد من تطبيقها بشكل صحيح
    print("جاري التأكد من تطبيق جميع الترحيلات...")
    try:
        call_command('migrate', '--noinput')
        print("تم التأكد من تطبيق جميع الترحيلات بنجاح.")
    except Exception as e:
        print(f"خطأ في تطبيق الترحيلات: {e}")

    # التحقق من اتصال قاعدة البيانات
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        if check_database_connection():
            break
        print(f"محاولة الاتصال بقاعدة البيانات... المحاولة {retry_count + 1}/{max_retries}")
        retry_count += 1
        time.sleep(2)  # انتظار 2 ثانية قبل المحاولة مرة أخرى

    if retry_count == max_retries:
        print("فشل الاتصال بقاعدة البيانات بعد عدة محاولات. إنهاء السكريبت.")
        return

    # تنفيذ ترحيلات قاعدة البيانات
    print("جاري تنفيذ ترحيلات قاعدة البيانات...")
    try:
        call_command('migrate', '--noinput')
        print("تم تنفيذ الترحيلات بنجاح.")
    except Exception as e:
        print(f"خطأ في تنفيذ الترحيلات: {e}")

    # التأكد من وجود الأقسام الافتراضية
    print("جاري التأكد من وجود الأقسام الافتراضية...")
    try:
        # إنشاء الأقسام الافتراضية أو تحديثها
        call_command('ensure_departments')
        print("تم إنشاء الأقسام الافتراضية بنجاح.")
    except Exception as e:
        print(f"خطأ في إنشاء الأقسام الافتراضية: {e}")

    # تنظيف الجلسات القديمة وإصلاح المستخدمين المكررين
    print("جاري تنظيف الجلسات القديمة وإصلاح المستخدمين المكررين...")
    try:
        # استخدام أمر تنظيف الجلسات المخصص
        call_command('cleanup_sessions', '--days=1', '--fix-users')
        print("تم تنظيف الجلسات القديمة وإصلاح المستخدمين المكررين بنجاح.")
    except Exception as e:
        print(f"خطأ في تنظيف الجلسات وإصلاح المستخدمين المكررين: {e}")

        # محاولة استخدام أمر تنظيف الجلسات الافتراضي
        try:
            call_command('clearsessions')
            print("تم تنظيف الجلسات القديمة باستخدام الأمر الافتراضي.")
        except Exception as inner_e:
            print(f"خطأ في تنظيف الجلسات باستخدام الأمر الافتراضي: {inner_e}")

    # إنشاء المستخدم الافتراضي أو إعادة تعيين كلمة المرور
    print("جاري إنشاء المستخدم الافتراضي أو إعادة تعيين كلمة المرور...")

    # محاولة إنشاء المستخدم الافتراضي بعدة طرق
    admin_created = False

    # الطريقة 1: استخدام أمر create_admin_user
    try:
        call_command('create_admin_user', '--force')
        print("تم إنشاء المستخدم الافتراضي أو إعادة تعيين كلمة المرور بنجاح باستخدام الأمر create_admin_user.")
        admin_created = True
    except Exception as e:
        print(f"خطأ في إنشاء المستخدم الافتراضي باستخدام الأمر create_admin_user: {e}")

    # الطريقة 2: استخدام نموذج المستخدم مباشرة
    if not admin_created:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # التحقق من وجود مستخدمين مكررين
            admin_users = User.objects.filter(username='admin')
            if admin_users.count() > 1:
                # حذف جميع المستخدمين المكررين باستثناء الأول
                for user in admin_users[1:]:
                    user.delete()
                print("تم حذف المستخدمين المكررين باسم 'admin'.")

            # إنشاء أو تحديث المستخدم الافتراضي
            admin_user = User.objects.filter(username='admin').first()
            if admin_user:
                admin_user.set_password('admin')
                admin_user.is_active = True
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.save()
                print("تم إعادة تعيين كلمة المرور للمستخدم الافتراضي يدويًا بنجاح.")
                admin_created = True
            else:
                User.objects.create_superuser('admin', 'admin@example.com', 'admin')
                print("تم إنشاء المستخدم الافتراضي يدويًا بنجاح.")
                admin_created = True
        except Exception as inner_e:
            print(f"خطأ في إنشاء المستخدم الافتراضي يدويًا: {inner_e}")

    # الطريقة 3: استخدام SQL مباشرة
    if not admin_created:
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # التحقق من وجود المستخدم
                cursor.execute("SELECT COUNT(*) FROM accounts_user WHERE username = 'admin'")
                count = cursor.fetchone()[0]

                if count > 0:
                    # تحديث كلمة المرور للمستخدم الموجود
                    # كلمة المرور المشفرة لـ 'admin'
                    hashed_password = 'pbkdf2_sha256$600000$5UAfuhrFEDxDyLABEL9Kcb$qRfbzrQZa6zYMr+NXH9sBK5AJMfVVe8aqZ1QlU+dUYE='
                    cursor.execute("""
                        UPDATE accounts_user
                        SET password = %s, is_active = TRUE, is_staff = TRUE, is_superuser = TRUE
                        WHERE username = 'admin'
                    """, [hashed_password])
                    print("تم إعادة تعيين كلمة المرور للمستخدم الافتراضي باستخدام SQL مباشرة.")
                else:
                    # إنشاء مستخدم جديد
                    hashed_password = 'pbkdf2_sha256$600000$5UAfuhrFEDxDyLABEL9Kcb$qRfbzrQZa6zYMr+NXH9sBK5AJMfVVe8aqZ1QlU+dUYE='
                    cursor.execute("""
                        INSERT INTO accounts_user (username, email, password, is_active, is_staff, is_superuser, date_joined, first_name, last_name)
                        VALUES ('admin', 'admin@example.com', %s, TRUE, TRUE, TRUE, NOW(), 'مدير', 'النظام')
                    """, [hashed_password])
                    print("تم إنشاء المستخدم الافتراضي باستخدام SQL مباشرة.")
                admin_created = True
        except Exception as sql_e:
            print(f"خطأ في إنشاء المستخدم الافتراضي باستخدام SQL مباشرة: {sql_e}")

    if admin_created:
        print("تم إنشاء المستخدم الافتراضي أو إعادة تعيين كلمة المرور بنجاح.")
    else:
        print("فشلت جميع محاولات إنشاء المستخدم الافتراضي أو إعادة تعيين كلمة المرور.")

    print("اكتمل تنفيذ سكريبت ما بعد النشر بنجاح.")

if __name__ == "__main__":
    main()
