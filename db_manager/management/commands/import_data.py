from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import subprocess
from db_manager.models import DatabaseConfig

class Command(BaseCommand):
    help = 'استيراد البيانات من ملف'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='مسار ملف البيانات')
        parser.add_argument('--db-config', type=int, help='معرف إعداد قاعدة البيانات')

    def handle(self, *args, **options):
        file_path = options['file_path']
        db_config_id = options.get('db_config')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'الملف {file_path} غير موجود'))
            return

        # تحديد نوع الملف
        is_json = file_path.lower().endswith('.json')
        is_dump = file_path.lower().endswith('.dump')

        if not (is_json or is_dump):
            self.stdout.write(self.style.ERROR('نوع الملف غير مدعوم. يجب أن يكون .json أو .dump'))
            return

        # الحصول على إعداد قاعدة البيانات
        if db_config_id:
            try:
                db_config = DatabaseConfig.objects.get(id=db_config_id)
            except DatabaseConfig.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'إعداد قاعدة البيانات بالمعرف {db_config_id} غير موجود'))
                return
        else:
            # استخدام قاعدة البيانات الافتراضية
            db_config = DatabaseConfig.objects.filter(is_default=True).first()
            if not db_config:
                self.stdout.write(self.style.ERROR('لا توجد قاعدة بيانات افتراضية'))
                return

        self.stdout.write(self.style.SUCCESS(f'جاري استيراد البيانات من {file_path} إلى قاعدة البيانات {db_config.name}'))

        try:
            # استيراد البيانات
            if is_json:
                # استخدام أمر Django loaddata
                call_command('loaddata', file_path)
                self.stdout.write(self.style.SUCCESS('تم استيراد البيانات بنجاح'))
            elif is_dump and db_config.db_type == 'postgresql':
                # تعيين متغيرات البيئة للاتصال بقاعدة البيانات
                os.environ['PGHOST'] = db_config.host
                os.environ['PGPORT'] = db_config.port or '5432'
                os.environ['PGDATABASE'] = db_config.database_name
                os.environ['PGUSER'] = db_config.username
                os.environ['PGPASSWORD'] = db_config.password

                # تنفيذ أمر pg_restore
                cmd = [
                    'pg_restore',
                    '--dbname=' + db_config.database_name,
                    '--clean',
                    '--if-exists',
                    '--jobs=4',  # استخدام 4 مهام متوازية لتسريع العملية
                    '--no-owner',  # تجاهل معلومات المالك
                    '--no-privileges',  # تجاهل الصلاحيات
                    file_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS('تم استيراد البيانات بنجاح'))
                else:
                    self.stdout.write(self.style.WARNING('تم استيراد البيانات مع بعض التحذيرات'))
                    self.stdout.write(result.stderr)
            else:
                self.stdout.write(self.style.ERROR('نوع قاعدة البيانات غير مدعوم للاستيراد'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'حدث خطأ أثناء استيراد البيانات: {str(e)}'))
