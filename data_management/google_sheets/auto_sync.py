from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from ..models import GoogleSheetsConfig, SyncLog
from .google_sheets_service import GoogleSheetsService

def auto_sync_data(force=False):
    """مهمة المزامنة التلقائية"""
    config = GoogleSheetsConfig.objects.filter(is_active=True).first()
    if not config:
        return False, 0
    
    # التحقق من وقت آخر مزامنة ومقارنته بالفاصل الزمني المحدد (تجاوز في حالة force=True)
    if not force and config.auto_sync_enabled is False:
        return False, 0
        
    if not force and config.last_sync:
        time_diff = timezone.now() - config.last_sync
        if time_diff < timedelta(minutes=config.sync_interval_minutes):
            return False, 0
    
    try:
        # إنشاء خدمة المزامنة
        sheets_service = GoogleSheetsService(config.credentials_file)
        
        # قائمة النماذج للمزامنة
        sync_models = []
        sync_details = []
        total_records = 0
        
        # إضافة النماذج المطلوبة للمزامنة
        if config.sync_customers:
            Customer = apps.get_model('customers', 'Customer')
            sync_models.append((Customer, 'العملاء'))
            
        if config.sync_orders:
            Order = apps.get_model('orders', 'Order')
            sync_models.append((Order, 'الطلبات'))
            
        if config.sync_products:
            Product = apps.get_model('inventory', 'Product')
            sync_models.append((Product, 'المنتجات'))
            
        if config.sync_inspections:
            Inspection = apps.get_model('inspections', 'Inspection')
            sync_models.append((Inspection, 'المعاينات'))
            
        if config.sync_installations:
            Installation = apps.get_model('installations', 'Installation')
            sync_models.append((Installation, 'التركيبات'))
        
        # تنفيذ المزامنة لكل نموذج
        for model, name in sync_models:
            try:
                count = sheets_service.sync_model_data(
                    spreadsheet_id=config.spreadsheet_id,
                    model_class=model,
                    sheet_name=name
                )
                sync_details.append(f'تم مزامنة {count} من {name} بنجاح.')
                total_records += count
            except Exception as e:
                sync_details.append(f'فشل مزامنة {name}: {str(e)}')
        
        # تسجيل المزامنة
        status = 'success' if all('فشل' not in d for d in sync_details) else 'partial'
        SyncLog.objects.create(
            status=status,
            details='\n'.join(sync_details),
            records_synced=total_records,
        )
        
        # تحديث وقت آخر مزامنة
        config.last_sync = timezone.now()
        config.save()
        return True, total_records
    
    except Exception as e:
        SyncLog.objects.create(
            status='failed',
            details=f'حدث خطأ أثناء المزامنة التلقائية: {str(e)}',
        )
        return False, 0