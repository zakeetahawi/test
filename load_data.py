import os
import django
import sys

# إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.core.management import call_command

def load_data():
    """تحميل البيانات من ملف JSON إلى قاعدة البيانات"""
    print("بدء تحميل البيانات...")
    
    try:
        # استخدام أمر loaddata لتحميل البيانات
        call_command('loaddata', 'data.json', verbosity=1)
        print("تم تحميل البيانات بنجاح!")
    except Exception as e:
        print(f"حدث خطأ أثناء تحميل البيانات: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    load_data()
