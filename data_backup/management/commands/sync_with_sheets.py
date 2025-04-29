from django.core.management.base import BaseCommand
from django.utils import timezone
from ...services.auto_sync_service import auto_sync_data

class Command(BaseCommand):
    help = 'مزامنة البيانات مع Google Sheets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='تجاوز فترة المزامنة وإجبار التنفيذ',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write(self.style.WARNING('بدء المزامنة مع Google Sheets...'))
        
        # تنفيذ المزامنة
        try:
            success, count = auto_sync_data(force=force)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'اكتملت المزامنة بنجاح! تم مزامنة {count} سجل.')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('فشلت المزامنة. راجع سجل المزامنة للمزيد من التفاصيل.')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'حدث خطأ أثناء تنفيذ المزامنة: {str(e)}')
            )