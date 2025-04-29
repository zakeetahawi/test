from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.apps import apps
from .models import GoogleSheetsConfig, SyncLog
from .services.google_sheets_service import GoogleSheetsService

@user_passes_test(lambda u: u.is_staff)
def backup_dashboard(request):
    """لوحة تحكم النسخ الاحتياطي والمزامنة"""
    config = GoogleSheetsConfig.objects.first()
    recent_logs = SyncLog.objects.all()[:10]
    
    context = {
        'config': config,
        'recent_logs': recent_logs,
        'title': 'لوحة تحكم النسخ الاحتياطي والمزامنة',
    }
    
    return render(request, 'data_backup/dashboard.html', context)

@user_passes_test(lambda u: u.is_staff)
def sync_now(request):
    """تشغيل المزامنة يدوياً"""
    config = GoogleSheetsConfig.objects.first()
    if not config:
        messages.error(request, 'لم يتم تكوين إعدادات المزامنة بعد.')
        return redirect('data_backup:dashboard')
        
    if not config.is_active:
        messages.error(request, 'المزامنة غير مفعلة حالياً.')
        return redirect('data_backup:dashboard')
    
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
            triggered_by=request.user
        )
        
        # تحديث وقت آخر مزامنة
        config.last_sync = timezone.now()
        config.save()
        
        messages.success(request, f'تمت المزامنة بنجاح! تم مزامنة {total_records} سجل.')
    
    except Exception as e:
        SyncLog.objects.create(
            status='failed',
            details=f'حدث خطأ أثناء المزامنة: {str(e)}',
            triggered_by=request.user
        )
        messages.error(request, f'فشلت المزامنة: {str(e)}')
    
    return redirect('data_backup:dashboard')

@user_passes_test(lambda u: u.is_staff)
def import_from_sheets(request):
    """استيراد البيانات من Google Sheets"""
    config = GoogleSheetsConfig.objects.first()
    if not config:
        messages.error(request, 'لم يتم تكوين إعدادات المزامنة بعد.')
        return redirect('data_backup:dashboard')
    
    if request.method == 'POST':
        model_name = request.POST.get('model')
        sheet_name = request.POST.get('sheet_name')
        
        if not model_name or not sheet_name:
            messages.error(request, 'يرجى تحديد النموذج واسم الورقة.')
            return redirect('data_backup:import_from_sheets')
        
        try:
            # الحصول على النموذج
            app_label, model_name = model_name.split('.')
            model_class = apps.get_model(app_label, model_name)
            
            # إنشاء خدمة المزامنة
            sheets_service = GoogleSheetsService(config.credentials_file)
            
            # استيراد البيانات
            count = sheets_service.import_data_from_sheet(
                spreadsheet_id=config.spreadsheet_id,
                sheet_name=sheet_name,
                model_class=model_class
            )
            
            # تسجيل الاستيراد
            SyncLog.objects.create(
                status='success',
                details=f'تم استيراد {count} سجل من {sheet_name} إلى {model_class._meta.verbose_name_plural}',
                records_synced=count,
                triggered_by=request.user
            )
            
            messages.success(request, f'تم استيراد {count} سجل بنجاح!')
        
        except Exception as e:
            SyncLog.objects.create(
                status='failed',
                details=f'فشل استيراد البيانات: {str(e)}',
                triggered_by=request.user
            )
            messages.error(request, f'فشل استيراد البيانات: {str(e)}')
        
        return redirect('data_backup:dashboard')
    
    # قائمة النماذج المتاحة للاستيراد
    available_models = []
    
    if config.sync_customers:
        Customer = apps.get_model('customers', 'Customer')
        available_models.append(('customers.Customer', 'العملاء', Customer._meta.verbose_name_plural))
        
    if config.sync_orders:
        Order = apps.get_model('orders', 'Order')
        available_models.append(('orders.Order', 'الطلبات', Order._meta.verbose_name_plural))
        
    if config.sync_products:
        Product = apps.get_model('inventory', 'Product')
        available_models.append(('inventory.Product', 'المنتجات', Product._meta.verbose_name_plural))
        
    if config.sync_inspections:
        Inspection = apps.get_model('inspections', 'Inspection')
        available_models.append(('inspections.Inspection', 'المعاينات', Inspection._meta.verbose_name_plural))
        
    if config.sync_installations:
        Installation = apps.get_model('installations', 'Installation')
        available_models.append(('installations.Installation', 'التركيبات', Installation._meta.verbose_name_plural))
    
    context = {
        'available_models': available_models,
        'title': 'استيراد البيانات من Google Sheets',
    }
    
    return render(request, 'data_backup/import_from_sheets.html', context)
