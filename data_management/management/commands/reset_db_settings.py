"""
أمر إدارة لإعادة تعيين إعدادات قاعدة البيانات
"""

import os
import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'إعادة تعيين إعدادات قاعدة البيانات'

    def add_arguments(self, parser):
        parser.add_argument(
            '--db-name',
            type=str,
            default='crm_system',
            help='اسم قاعدة البيانات',
        )
        parser.add_argument(
            '--db-user',
            type=str,
            default='postgres',
            help='اسم المستخدم',
        )
        parser.add_argument(
            '--db-password',
            type=str,
            default='5525',
            help='كلمة المرور',
        )
        parser.add_argument(
            '--db-host',
            type=str,
            default='localhost',
            help='المضيف',
        )
        parser.add_argument(
            '--db-port',
            type=str,
            default='5432',
            help='المنفذ',
        )

    def handle(self, *args, **options):
        # الحصول على مسار المشروع
        BASE_DIR = Path(settings.BASE_DIR)
        
        # مسار ملف إعدادات قاعدة البيانات
        DB_SETTINGS_FILE = os.path.join(BASE_DIR, 'db_settings.json')
        
        # إنشاء إعدادات قاعدة البيانات الجديدة
        db_settings = {
            "active_db": 1,
            "databases": {
                "1": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": options['db_name'],
                    "USER": options['db_user'],
                    "PASSWORD": options['db_password'],
                    "HOST": options['db_host'],
                    "PORT": options['db_port']
                }
            }
        }
        
        # حفظ إعدادات قاعدة البيانات
        try:
            with open(DB_SETTINGS_FILE, 'w') as f:
                json.dump(db_settings, f, indent=4)
            
            self.stdout.write(self.style.SUCCESS('تم إعادة تعيين إعدادات قاعدة البيانات بنجاح.'))
            self.stdout.write(self.style.SUCCESS(f'اسم قاعدة البيانات: {options["db_name"]}'))
            self.stdout.write(self.style.SUCCESS(f'اسم المستخدم: {options["db_user"]}'))
            self.stdout.write(self.style.SUCCESS(f'المضيف: {options["db_host"]}'))
            self.stdout.write(self.style.SUCCESS(f'المنفذ: {options["db_port"]}'))
            self.stdout.write(self.style.SUCCESS('يرجى إعادة تشغيل السيرفر لتطبيق التغييرات.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'حدث خطأ أثناء إعادة تعيين إعدادات قاعدة البيانات: {str(e)}'))
