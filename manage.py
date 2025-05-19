#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # إعداد متغيرات البيئة لقاعدة بيانات Railway
    if 'POSTGRES_PASSWORD' in os.environ:
        print("تم اكتشاف بيئة Railway في manage.py")
        # تعيين متغيرات البيئة لقاعدة البيانات
        os.environ['DATABASE_URL'] = f"postgresql://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('RAILWAY_PRIVATE_DOMAIN')}:5432/{os.environ.get('POSTGRES_DB')}"
        print(f"تم تعيين DATABASE_URL: {os.environ.get('DATABASE_URL')}")

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # تنفيذ الترحيلات تلقائيًا عند تشغيل السيرفر
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        # تعيين متغير بيئي لتجنب تنفيذ الترحيلات مرتين
        if not os.environ.get('AUTO_MIGRATE_EXECUTED'):
            try:
                # تأكد من أن Django تم تهيئته بالكامل
                import django
                django.setup()

                # تنفيذ أمر auto_migrate
                from django.core.management import call_command
                print("جاري تنفيذ الترحيلات تلقائيًا...")
                call_command('auto_migrate')
                print("تم تنفيذ الترحيلات بنجاح.")

                # تعيين متغير بيئي لتجنب تنفيذ الترحيلات مرتين
                os.environ['AUTO_MIGRATE_EXECUTED'] = '1'
            except Exception as e:
                print(f"حدث خطأ أثناء تنفيذ الترحيلات التلقائية: {str(e)}")

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
