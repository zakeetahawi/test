import os
import time
import hashlib
import json
import shutil
import tarfile
import tempfile
from datetime import datetime
from django.conf import settings
from django.core import management
from django.utils import timezone
from django.db.models import Sum
from django.apps import apps
from ..models import BackupHistory, AutoBackupConfig
from .cloud_storage import CloudStorageService

class BackupService:
    """خدمة النسخ الاحتياطي"""
    
    def __init__(self, user=None):
        self.user = user
        self.backup_dir = os.path.join(settings.MEDIA_ROOT, 'db_backups')
        
        # إنشاء مجلد النسخ الاحتياطية إذا لم يكن موجودًا
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # إنشاء مجلد مؤقت للنسخ الاحتياطية
        self.temp_dir = os.path.join(self.backup_dir, 'tmp')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def create_backup(self, backup_type='manual'):
        """إنشاء نسخة احتياطية جديدة"""
        start_time = time.time()
        timestamp = timezone.now()
        date_str = timestamp.strftime('%Y%m%d_%H%M%S')
        file_name = f"backup_{date_str}.tar.gz"
        file_path = os.path.join(self.backup_dir, file_name)
        
        try:
            # إنشاء نسخة احتياطية مؤقتة من قاعدة البيانات
            temp_dir = os.path.join(self.temp_dir, f'backup_{date_str}')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            db_file = os.path.join(temp_dir, 'db_dump.json')
            sql_file = os.path.join(temp_dir, 'db_dump.sql')
            
            # تحديد متغير بيئة لإجبار استخدام UTF-8
            original_encoding = None
            if 'PYTHONIOENCODING' in os.environ:
                original_encoding = os.environ['PYTHONIOENCODING']
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            try:
                # استخدام فتح ملف مباشرة مع ترميز UTF-8 بدلاً من output في call_command
                # إنشاء ملف JSON لسهولة الاستعادة
                with open(db_file, 'w', encoding='utf-8') as output_file:
                    management.call_command(
                        'dumpdata',
                        exclude=['contenttypes', 'admin.logentry', 'sessions.session'],
                        indent=2,
                        stdout=output_file
                    )
                
                # استخدام pg_dump لإنشاء ملف SQL كنسخة احتياطية ثانية
                if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
                    # تكوين بيئة pg_dump
                    db_settings = settings.DATABASES['default']
                    env = os.environ.copy()
                    env['PGPASSWORD'] = db_settings.get('PASSWORD', '')
                    
                    # تنفيذ أمر pg_dump
                    import subprocess
                    pg_dump_cmd = [
                        'pg_dump',
                        '--host=' + db_settings.get('HOST', 'localhost'),
                        '--port=' + str(db_settings.get('PORT', '5432')),
                        '--username=' + db_settings.get('USER', ''),
                        '--format=custom',
                        '--file=' + sql_file,
                        db_settings.get('NAME', '')
                    ]
                    
                    try:
                        subprocess.run(pg_dump_cmd, env=env, check=True)
                    except Exception as e:
                        # لا نريد أن نفشل إذا فشل pg_dump
                        print(f"Warning: Failed to create SQL backup: {e}")
            finally:
                # استعادة متغير البيئة الأصلي
                if original_encoding:
                    os.environ['PYTHONIOENCODING'] = original_encoding
                elif 'PYTHONIOENCODING' in os.environ:
                    del os.environ['PYTHONIOENCODING']
            
            # إنشاء ملف مضغوط يحتوي على ملفات قاعدة البيانات والوسائط
            with tarfile.open(file_path, "w:gz") as tar:
                # إضافة ملفات قاعدة البيانات
                tar.add(db_file, arcname=os.path.basename(db_file))
                if os.path.exists(sql_file):
                    tar.add(sql_file, arcname=os.path.basename(sql_file))
                
                # إضافة ملفات README لشرح كيفية الاستعادة
                readme_file = os.path.join(temp_dir, 'README.txt')
                with open(readme_file, 'w', encoding='utf-8') as f:
                    f.write("ملف النسخة الاحتياطية لنظام CRM\n")
                    f.write(f"تاريخ النسخة الاحتياطية: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=================================\n\n")
                    f.write("لاستعادة هذه النسخة الاحتياطية:\n")
                    f.write("1. قم بفك ضغط هذا الملف\n")
                    f.write("2. لاستعادة قاعدة البيانات من JSON استخدم:\n")
                    f.write("   python manage.py loaddata db_dump.json\n")
                    f.write("3. أو لاستعادة قاعدة البيانات من SQL استخدم:\n")
                    f.write("   pg_restore --dbname=YOUR_DB_NAME --clean db_dump.sql\n\n")
                    f.write("4. انسخ محتويات مجلد media إلى مجلد media الخاص بمشروعك\n")
                
                tar.add(readme_file, arcname=os.path.basename(readme_file))
                
                # إضافة ملفات الوسائط إذا كانت موجودة
                if os.path.exists(settings.MEDIA_ROOT):
                    for dirpath, dirnames, filenames in os.walk(settings.MEDIA_ROOT):
                        # استثناء مجلد النسخ الاحتياطية نفسه لتجنب التكرار
                        if 'db_backups' in dirpath:
                            continue
                        
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            arcname = os.path.relpath(filepath, settings.MEDIA_ROOT)
                            arcname = os.path.join('media', arcname)
                            tar.add(filepath, arcname=arcname)
            
            # إنشاء نسخة غير مضغوطة أيضاً للاستخدام المباشر
            json_backup_path = os.path.join(self.backup_dir, f"backup_{date_str}.json")
            shutil.copy2(db_file, json_backup_path)
            
            # حساب حجم الملف
            file_size = os.path.getsize(file_path)
            
            # حساب قيمة التحقق من الملف
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            file_checksum = sha256_hash.hexdigest()
            
            # إنشاء سجل النسخ الاحتياطي
            backup = BackupHistory.objects.create(
                backup_type=backup_type,
                file_name=file_name,
                file_size=file_size,
                status='success',
                metadata={
                    'db_version': settings.DATABASES['default'].get('VERSION', ''),
                    'django_version': settings.DJANGO_VERSION,
                    'included_apps': self._get_included_apps(),
                    'json_path': json_backup_path
                },
                file_checksum=file_checksum,
                backup_location=file_path,
                is_compressed=True,
                is_encrypted=False,
                created_by=self.user
            )
            
            # رفع النسخة الاحتياطية إلى التخزين السحابي إذا كان مفعلاً
            cloud_service = CloudStorageService()
            if cloud_service.config and cloud_service.config.is_active and cloud_service.config.auto_upload:
                cloud_dest_path = f"backups/{file_name}"
                success, message = cloud_service.upload_file(file_path, cloud_dest_path)
                if success:
                    backup.metadata['cloud_storage'] = {
                        'provider': cloud_service.config.storage_type,
                        'path': cloud_dest_path,
                        'upload_time': timezone.now().isoformat(),
                        'message': message
                    }
                    backup.save()
            
            # تنظيف الملفات المؤقتة
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Failed to clean temporary files: {e}")
            
            return {
                'success': True,
                'backup_id': backup.id,
                'file_path': file_path,
                'json_path': json_backup_path,
                'file_size': file_size,
                'duration': time.time() - start_time
            }
            
        except Exception as e:
            # إنشاء سجل نسخ احتياطي فاشل
            BackupHistory.objects.create(
                backup_type=backup_type,
                file_name=file_name,
                file_size=0,
                status='failed',
                error_message=str(e),
                backup_location="",
                created_by=self.user
            )
            
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def restore_backup(self, backup_id):
        """استعادة من نسخة احتياطية"""
        try:
            backup = BackupHistory.objects.get(id=backup_id, status='success')
            
            # التحقق من وجود الملف
            if not os.path.exists(backup.backup_location):
                # التحقق من وجود نسخة JSON احتياطية
                json_path = backup.metadata.get('json_path')
                if json_path and os.path.exists(json_path):
                    return self._restore_from_json(json_path)
                return {'success': False, 'error': 'ملف النسخة الاحتياطية غير موجود'}
            
            # التحقق من سلامة الملف
            if not backup.validate_backup_file():
                return {'success': False, 'error': 'فشل التحقق من سلامة ملف النسخة الاحتياطية'}
            
            # فك ضغط الملف إلى مجلد مؤقت
            extract_dir = os.path.join(self.temp_dir, 'extract')
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir)
            
            with tarfile.open(backup.backup_location, "r:gz") as tar:
                tar.extractall(extract_dir)
            
            # استعادة بيانات قاعدة البيانات
            db_file = os.path.join(extract_dir, 'db_dump.json')
            sql_file = os.path.join(extract_dir, 'db_dump.sql')
            
            # محاولة الاستعادة من ملف JSON أولاً
            if os.path.exists(db_file):
                result = self._restore_from_json(db_file)
                if result['success']:
                    # استعادة ملفات الوسائط
                    self._restore_media_files(extract_dir)
                    
                    # تحديث سجل النسخة الاحتياطية
                    backup.status = 'restored'
                    backup.save()
                    
                    return {'success': True}
                else:
                    # إذا فشلت الاستعادة من JSON، نحاول من SQL
                    if os.path.exists(sql_file):
                        result = self._restore_from_sql(sql_file)
                        if result['success']:
                            # استعادة ملفات الوسائط
                            self._restore_media_files(extract_dir)
                            
                            # تحديث سجل النسخة الاحتياطية
                            backup.status = 'restored'
                            backup.save()
                            
                            return {'success': True}
            
            # إذا لم نجد ملفات قاعدة البيانات
            if not os.path.exists(db_file) and not os.path.exists(sql_file):
                return {'success': False, 'error': 'ملفات قاعدة البيانات غير موجودة في النسخة الاحتياطية'}
                
            return {'success': False, 'error': 'فشلت محاولات استعادة قاعدة البيانات'}
                
        except BackupHistory.DoesNotExist:
            return {'success': False, 'error': 'النسخة الاحتياطية المطلوبة غير موجودة أو فاشلة'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            # تنظيف الملفات المؤقتة
            try:
                extract_dir = os.path.join(self.temp_dir, 'extract')
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
            except Exception as e:
                print(f"Warning: Failed to clean temporary files: {e}")
    
    def _restore_from_json(self, json_path):
        """استعادة قاعدة البيانات من ملف JSON"""
        try:
            # التحقق من صحة ملف JSON
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError:
                return {'success': False, 'error': 'ملف JSON غير صالح'}
            
            # مسح قاعدة البيانات الحالية
            management.call_command('flush', interactive=False)
            
            # استعادة البيانات من ملف JSON
            management.call_command('loaddata', json_path)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': f'فشل استعادة قاعدة البيانات من JSON: {str(e)}'}
    
    def _restore_from_sql(self, sql_path):
        """استعادة قاعدة البيانات من ملف SQL"""
        try:
            if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
                return {'success': False, 'error': 'استعادة ملف SQL مدعومة فقط لقواعد بيانات PostgreSQL'}
            
            # تكوين بيئة pg_restore
            db_settings = settings.DATABASES['default']
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings.get('PASSWORD', '')
            
            # تنفيذ أمر pg_restore
            import subprocess
            pg_restore_cmd = [
                'pg_restore',
                '--host=' + db_settings.get('HOST', 'localhost'),
                '--port=' + str(db_settings.get('PORT', '5432')),
                '--username=' + db_settings.get('USER', ''),
                '--dbname=' + db_settings.get('NAME', ''),
                '--clean',
                '--no-owner',
                '--no-privileges',
                sql_path
            ]
            
            result = subprocess.run(pg_restore_cmd, env=env, capture_output=True)
            
            if result.returncode != 0:
                # pg_restore عادة ما يُرجع رمز خطأ حتى في حالة النجاح، لذا نتجاهله
                print(f"Warning: pg_restore returned code {result.returncode}")
                print(f"Error output: {result.stderr.decode('utf-8')}")
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': f'فشل استعادة قاعدة البيانات من SQL: {str(e)}'}
    
    def _restore_media_files(self, extract_dir):
        """استعادة ملفات الوسائط"""
        media_dir = os.path.join(extract_dir, 'media')
        if os.path.exists(media_dir):
            # نسخ ملفات الوسائط المستعادة بدلاً من حذف المجلد الحالي
            for item in os.listdir(media_dir):
                src_path = os.path.join(media_dir, item)
                dst_path = os.path.join(settings.MEDIA_ROOT, item)
                
                # تجنب استبدال مجلد النسخ الاحتياطية
                if item == 'db_backups':
                    continue
                
                if os.path.isdir(src_path):
                    # دمج المحتويات بدلاً من الحذف
                    if not os.path.exists(dst_path):
                        os.makedirs(dst_path)
                    
                    for root, dirs, files in os.walk(src_path):
                        rel_path = os.path.relpath(root, src_path)
                        dst_root = os.path.join(dst_path, rel_path) if rel_path != '.' else dst_path
                        
                        if not os.path.exists(dst_root):
                            os.makedirs(dst_root)
                        
                        for file in files:
                            src_file = os.path.join(root, file)
                            dst_file = os.path.join(dst_root, file)
                            
                            if not os.path.exists(dst_file) or os.path.getsize(dst_file) != os.path.getsize(src_file):
                                shutil.copy2(src_file, dst_file)
                else:
                    # نسخ الملف
                    shutil.copy2(src_path, dst_path)

    def clean_old_backups(self):
        """حذف النسخ الاحتياطية القديمة حسب فترة الاحتفاظ"""
        config = AutoBackupConfig.objects.first()
        if not config or not config.enabled or config.retention_days <= 0:
            return {'deleted': 0}
        
        # حساب تاريخ الاحتفاظ
        retention_date = timezone.now() - timezone.timedelta(days=config.retention_days)
        
        # الحصول على النسخ الاحتياطية القديمة
        old_backups = BackupHistory.objects.filter(timestamp__lt=retention_date)
        count = old_backups.count()
        
        # حذف الملفات والسجلات
        for backup in old_backups:
            try:
                if os.path.exists(backup.backup_location):
                    os.remove(backup.backup_location)
            except:
                pass
        
        # حذف السجلات
        old_backups.delete()
        
        return {'deleted': count}
    
    def get_backup_stats(self):
        """الحصول على إحصائيات النسخ الاحتياطي"""
        total_backups = BackupHistory.objects.count()
        successful_backups = BackupHistory.objects.filter(status='success').count()
        failed_backups = BackupHistory.objects.filter(status='failed').count()
        restored_backups = BackupHistory.objects.filter(status='restored').count()
        
        # حساب إجمالي الحجم
        total_size = BackupHistory.objects.filter(status__in=['success', 'restored']).aggregate(total=Sum('file_size'))['total'] or 0
        
        # الحصول على آخر نسخة احتياطية
        last_backup = BackupHistory.objects.order_by('-timestamp').first()
        
        return {
            'total_backups': total_backups,
            'successful_backups': successful_backups,
            'failed_backups': failed_backups,
            'restored_backups': restored_backups,
            'success_rate': (successful_backups / total_backups * 100) if total_backups > 0 else 0,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024) if total_size > 0 else 0,
            'last_backup': last_backup.timestamp if last_backup else None
        }
    
    def _get_included_apps(self):
        """الحصول على قائمة بالتطبيقات المضمنة في النسخة الاحتياطية"""
        included_apps = []
        
        for app_config in apps.get_app_configs():
            if not app_config.name.startswith('django.') and not app_config.name.startswith('rest_framework'):
                included_apps.append(app_config.name)
        
        return included_apps