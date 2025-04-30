from django.core.management.base import BaseCommand
import time
import threading
from django.utils import timezone
from datetime import timedelta
from ...models import GoogleSheetsConfig
from ...services.auto_sync_service import auto_sync_data
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'تشغيل خدمة المزامنة التلقائية مع Google Sheets في الخلفية'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('بدء خدمة المزامنة التلقائية مع Google Sheets...'))
        
        try:
            # بدء حلقة المزامنة في الخلفية
            sync_thread = threading.Thread(target=self._sync_loop)
            sync_thread.daemon = True
            sync_thread.start()
            
            # الاستمرار في تشغيل الخدمة حتى يتم إيقافها يدويًا
            while not self._stop_event.is_set():
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('تم إيقاف خدمة المزامنة...'))
            self._stop_event.set()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'حدث خطأ: {str(e)}'))
            self._stop_event.set()
    
    def _sync_loop(self):
        """حلقة التزامن المستمرة في الخلفية"""
        while not self._stop_event.is_set():
            try:
                # التحقق من الإعدادات واجراء المزامنة
                config = GoogleSheetsConfig.objects.filter(is_active=True).first()
                if config and config.auto_sync_enabled:
                    # التحقق إذا كان الوقت قد حان للمزامنة التالية
                    if not config.last_sync or config.last_sync + timedelta(minutes=config.sync_interval_minutes) <= timezone.now():
                        self.stdout.write(self.style.WARNING('جاري تنفيذ المزامنة التلقائية...'))
                        success, count = auto_sync_data(force=False)
                        if success:
                            self.stdout.write(self.style.SUCCESS(f'اكتملت المزامنة بنجاح! تم مزامنة {count} سجل.'))
                        else:
                            self.stdout.write(self.style.ERROR('لم تكن المزامنة مطلوبة في هذا الوقت أو فشلت.'))
            except Exception as e:
                logger.error(f"خطأ في حلقة المزامنة: {str(e)}")
                self.stdout.write(self.style.ERROR(f'حدث خطأ أثناء المزامنة التلقائية: {str(e)}'))
            
            # انتظار 60 ثانية قبل التحقق مرة أخرى (يمكننا التحقق كل دقيقة بدلاً من الانتظار لفترة المزامنة الكاملة)
            for _ in range(60):
                if self._stop_event.is_set():
                    break
                time.sleep(1)