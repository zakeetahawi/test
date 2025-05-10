import os
import boto3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q
from ..models import CloudStorageConfig, BackupMetrics
import logging

logger = logging.getLogger(__name__)

class CloudStorageService:
    """خدمة التعامل مع التخزين السحابي"""
    
    def __init__(self):
        self.config = CloudStorageConfig.objects.first()
        
    def upload_file(self, file_path, destination_path=None):
        """رفع ملف إلى التخزين السحابي"""
        if not self.config or not self.config.is_active:
            return False, "التخزين السحابي غير مفعل"
            
        start_time = timezone.now()
        success = False
        error_message = None
        
        try:
            if self.config.storage_type == 'google_drive':
                success, error_message = self._upload_to_google_drive(file_path, destination_path)
            elif self.config.storage_type == 's3':
                success, error_message = self._upload_to_s3(file_path, destination_path)
                
            # تسجيل المقاييس
            duration = (timezone.now() - start_time).total_seconds()
            BackupMetrics.objects.create(
                backup_size=os.path.getsize(file_path),
                successful=success,
                duration=duration,
                storage_type=self.config.storage_type,
                error_message=error_message if not success else None
            )
            
            return success, error_message
            
        except Exception as e:
            logger.exception("فشل رفع الملف إلى التخزين السحابي")
            return False, str(e)
    
    def _upload_to_google_drive(self, file_path, destination_path=None):
        """رفع ملف إلى Google Drive"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                os.path.join(settings.MEDIA_ROOT, self.config.google_credentials.name),
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            service = build('drive', 'v3', credentials=credentials)
            
            file_metadata = {
                'name': os.path.basename(destination_path or file_path),
                'parents': [self.config.google_folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return True, file.get('id')
            
        except Exception as e:
            logger.exception("فشل الرفع إلى Google Drive")
            return False, str(e)
    
    def _upload_to_s3(self, file_path, destination_path=None):
        """رفع ملف إلى Amazon S3"""
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.aws_access_key,
                aws_secret_access_key=self.config.aws_secret_key,
                region_name=self.config.aws_region
            )
            
            dest_path = destination_path or os.path.basename(file_path)
            s3_client.upload_file(
                file_path,
                self.config.aws_bucket_name,
                dest_path
            )
            
            return True, f"s3://{self.config.aws_bucket_name}/{dest_path}"
            
        except Exception as e:
            logger.exception("فشل الرفع إلى Amazon S3")
            return False, str(e)
    
    def test_connection(self):
        """اختبار الاتصال بالتخزين السحابي"""
        if not self.config or not self.config.is_active:
            return False, "التخزين السحابي غير مفعل"
            
        try:
            if self.config.storage_type == 'google_drive':
                credentials = service_account.Credentials.from_service_account_file(
                    os.path.join(settings.MEDIA_ROOT, self.config.google_credentials.name),
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                service = build('drive', 'v3', credentials=credentials)
                service.files().list(pageSize=1).execute()
                return True, "تم الاتصال بنجاح مع Google Drive"
                
            elif self.config.storage_type == 's3':
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.config.aws_access_key,
                    aws_secret_access_key=self.config.aws_secret_key,
                    region_name=self.config.aws_region
                )
                s3_client.list_objects_v2(
                    Bucket=self.config.aws_bucket_name,
                    MaxKeys=1
                )
                return True, "تم الاتصال بنجاح مع Amazon S3"
                
        except Exception as e:
            logger.exception("فشل اختبار الاتصال بالتخزين السحابي")
            return False, str(e)
            
    @staticmethod
    def get_storage_metrics(days=30):
        """الحصول على مقاييس التخزين"""
        start_date = timezone.now() - timezone.timedelta(days=days)
        metrics = BackupMetrics.objects.filter(backup_date__gte=start_date)
        
        total_backups = metrics.count()
        successful_backups = metrics.filter(successful=True).count()
        
        # الحصول على سجلات المقاييس المفصلة
        metrics_list = metrics.order_by('-backup_date')[:100]  # عرض آخر 100 سجل كحد أقصى
        
        return {
            'success_rate': (successful_backups / total_backups * 100) if total_backups > 0 else 0,
            'average_duration': metrics.filter(successful=True).aggregate(avg=Avg('duration'))['avg'] or 0,
            'total_size': metrics.aggregate(sum=Sum('backup_size'))['sum'] or 0,
            'backup_count': total_backups,
            'metrics_list': metrics_list
        }
        
    @staticmethod
    def get_metrics_by_date_range(start_date, end_date):
        """الحصول على المقاييس حسب نطاق تاريخي محدد"""
        metrics = BackupMetrics.objects.filter(
            backup_date__range=(start_date, end_date)
        )
        
        # إحصائيات مجمعة
        stats = {
            'total': metrics.count(),
            'successful': metrics.filter(successful=True).count(),
            'failed': metrics.filter(successful=False).count(),
            'success_rate': 0,
            'average_duration': 0,
            'total_size': 0,
            'by_storage_type': {}
        }
        
        if stats['total'] > 0:
            stats['success_rate'] = (stats['successful'] / stats['total']) * 100
            stats['average_duration'] = metrics.filter(successful=True).aggregate(avg=Avg('duration'))['avg'] or 0
            stats['total_size'] = metrics.aggregate(sum=Sum('backup_size'))['sum'] or 0
            
            # تجميع حسب نوع التخزين
            storage_types = metrics.values('storage_type').annotate(
                count=Count('id'),
                successful=Count('id', filter=Q(successful=True)),
                failed=Count('id', filter=Q(successful=False)),
                total_size=Sum('backup_size'),
                avg_duration=Avg('duration', filter=Q(successful=True))
            )
            
            for st in storage_types:
                stats['by_storage_type'][st['storage_type']] = {
                    'count': st['count'],
                    'successful': st['successful'],
                    'failed': st['failed'],
                    'success_rate': (st['successful'] / st['count']) * 100 if st['count'] > 0 else 0,
                    'total_size': st['total_size'] or 0,
                    'avg_duration': st['avg_duration'] or 0
                }
                
        return stats