"""
أمر إدارة لإعادة تشغيل السيرفر
"""

import os
import sys
import time
import logging
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'إعادة تشغيل السيرفر'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='المنفذ الذي سيتم تشغيل السيرفر عليه',
        )
        parser.add_argument(
            '--host',
            type=str,
            default='127.0.0.1',
            help='المضيف الذي سيتم تشغيل السيرفر عليه',
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=2,
            help='التأخير بالثواني قبل إعادة تشغيل السيرفر',
        )

    def handle(self, *args, **options):
        port = options.get('port', 8000)
        host = options.get('host', '127.0.0.1')
        delay = options.get('delay', 2)
        
        self.stdout.write(self.style.SUCCESS(f'جاري إعادة تشغيل السيرفر على {host}:{port} بعد {delay} ثواني...'))
        
        # انتظار لفترة قصيرة
        time.sleep(delay)
        
        # الحصول على مسار Python الحالي
        python_executable = sys.executable
        
        # إعادة تشغيل السيرفر في عملية منفصلة
        try:
            # إنهاء العمليات الحالية (في نظام Windows)
            if os.name == 'nt':
                try:
                    subprocess.run(f'taskkill /F /PID {os.getpid()} /T', shell=True)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'فشل إنهاء العمليات الحالية: {e}'))
            
            # إعادة تشغيل السيرفر
            cmd = [
                python_executable,
                'manage.py',
                'runserver',
                f'{host}:{port}',
                '--noreload'
            ]
            
            self.stdout.write(self.style.SUCCESS(f'تنفيذ الأمر: {" ".join(cmd)}'))
            
            # تنفيذ الأمر في عملية منفصلة
            subprocess.Popen(
                cmd,
                close_fds=True,
                shell=False,
                cwd=settings.BASE_DIR
            )
            
            self.stdout.write(self.style.SUCCESS('تم طلب إعادة تشغيل السيرفر بنجاح'))
            
            # إنهاء العملية الحالية
            os._exit(0)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'حدث خطأ أثناء إعادة تشغيل السيرفر: {e}'))
