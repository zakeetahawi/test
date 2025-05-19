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

    # تنظيف الجلسات القديمة
    print("جاري تنظيف الجلسات القديمة...")
    try:
        call_command('clearsessions')
        print("تم تنظيف الجلسات القديمة بنجاح.")
    except Exception as e:
        print(f"خطأ في تنظيف الجلسات: {e}")

    print("اكتمل تنفيذ سكريبت ما بعد النشر بنجاح.")

if __name__ == "__main__":
    main()
