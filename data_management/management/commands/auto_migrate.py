"""
أمر إدارة لتنفيذ الترحيلات وإنشاء مستخدم مدير افتراضي تلقائيًا
"""

import os
import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'تنفيذ الترحيلات وإنشاء مستخدم مدير افتراضي تلقائيًا'

    def handle(self, *args, **options):
        try:
            # تنفيذ الترحيلات
            self.stdout.write(self.style.WARNING('جاري تنفيذ الترحيلات...'))
            call_command('migrate', '--noinput')
            self.stdout.write(self.style.SUCCESS('تم تنفيذ الترحيلات بنجاح.'))
            
            # إنشاء مستخدم مدير افتراضي إذا لم يكن هناك مستخدمين
            User = get_user_model()
            if User.objects.count() == 0:
                self.stdout.write(self.style.WARNING('جاري إنشاء مستخدم مدير افتراضي...'))
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin'
                )
                self.stdout.write(self.style.SUCCESS('تم إنشاء مستخدم مدير افتراضي (اسم المستخدم: admin، كلمة المرور: admin) بنجاح.'))
            else:
                self.stdout.write(self.style.SUCCESS('يوجد مستخدمين بالفعل، تم تخطي إنشاء مستخدم مدير افتراضي.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'حدث خطأ أثناء تنفيذ الترحيلات: {str(e)}'))
