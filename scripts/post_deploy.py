#!/usr/bin/env python
"""
سكريبت ما بعد النشر - يتم تنفيذه تلقائيًا بعد نشر التطبيق
يقوم بإنشاء الأقسام الافتراضية إذا لم تكن موجودة
"""

import os
import sys
import django

# إضافة المسار الحالي إلى مسار النظام
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.core.management import call_command

def main():
    """
    الوظيفة الرئيسية للسكريبت
    """
    print("بدء تنفيذ سكريبت ما بعد النشر...")

    # التأكد من وجود الأقسام الافتراضية
    print("جاري التأكد من وجود الأقسام الافتراضية...")
    # إنشاء الأقسام الافتراضية أو تحديثها
    call_command('ensure_departments')

    print("اكتمل تنفيذ سكريبت ما بعد النشر بنجاح.")

if __name__ == "__main__":
    main()
