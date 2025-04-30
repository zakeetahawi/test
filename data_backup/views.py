from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.apps import apps
from django.conf import settings
from .models import GoogleSheetsConfig, SyncLog
from .services.google_sheets_service import GoogleSheetsService
from .forms import SyncIntervalForm, GoogleSheetsImportForm

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
        
        # مزامنة معلومات الشركة - استخدام نموذج CompanyInfo وباقي النماذج المرتبطة من تطبيق accounts
        if config.sync_company_info:
            try:
                CompanyInfo = apps.get_model('accounts', 'CompanyInfo')
                company_data = CompanyInfo.objects.all()
                
                # استدعاء النماذج الجديدة
                ContactFormSettings = apps.get_model('accounts', 'ContactFormSettings')
                FooterSettings = apps.get_model('accounts', 'FooterSettings')
                
                # إعداد مصفوفة البيانات المجمعة لصفحة "معلومات النظام" الشاملة
                system_info_data = []
                
                # إضافة العناوين للجدول المجمع
                system_info_headers = ['القسم', 'المعرف', 'الاسم', 'القيمة']
                system_info_data.append(system_info_headers)
                
                if company_data.exists():
                    try:
                        # إضافة بيانات من نموذج معلومات الشركة
                        company_info = CompanyInfo.objects.first()
                        if company_info:
                            for field in company_info._meta.fields:
                                if field.name not in ['id', 'version', 'release_date', 'developer']:
                                    value = getattr(company_info, field.name)
                                    # تنسيق القيم المعقدة مثل الصور أو JSON
                                    if field.name == 'logo' and value:
                                        value = value.url if value else ''
                                    elif field.name == 'social_links' and value:
                                        import json
                                        value = json.dumps(value, ensure_ascii=False)
                                    system_info_data.append(['معلومات الشركة', 'CompanyInfo', field.verbose_name, str(value)])
                        
                        # إضافة بيانات من نموذج إعدادات الاتصال
                        contact_settings = ContactFormSettings.objects.first()
                        if contact_settings:
                            for field in contact_settings._meta.fields:
                                if field.name != 'id':
                                    value = getattr(contact_settings, field.name)
                                    system_info_data.append(['إعدادات الاتصال', 'ContactFormSettings', field.verbose_name, str(value)])
                        
                        # إضافة بيانات من نموذج إعدادات التذييل
                        footer_settings = FooterSettings.objects.first()
                        if footer_settings:
                            for field in footer_settings._meta.fields:
                                if field.name != 'id':
                                    value = getattr(footer_settings, field.name)
                                    system_info_data.append(['إعدادات التذييل', 'FooterSettings', field.verbose_name, str(value)])
                        
                        # تم استبعاد إعدادات صفحة عن النظام من المزامنة بناء على طلب المستخدم
                        # لا يتم إضافة أي بيانات من نموذج AboutPageSettings
                        
                        # إنشاء أو تحديث ورقة معلومات النظام المجمعة
                        sheets_service.create_or_update_sheet(
                            spreadsheet_id=config.spreadsheet_id,
                            sheet_name='معلومات النظام',
                            data=system_info_data
                        )
                        
                        sync_details.append(f'تم مزامنة معلومات النظام الشاملة بنجاح ({len(system_info_data)-1} سجل).')
                        total_records += len(system_info_data) - 1  # نطرح 1 لأن السطر الأول هو العناوين
                    except Exception as e:
                        sync_details.append(f'فشل مزامنة معلومات النظام: {str(e)}')
                else:
                    # إنشاء ورقة معلومات النظام فارغة مع العناوين فقط إذا لم تكن هناك بيانات
                    try:
                        sheets_service.create_or_update_sheet(
                            spreadsheet_id=config.spreadsheet_id,
                            sheet_name='معلومات النظام',
                            data=[system_info_headers]
                        )
                        
                        sync_details.append(f'تم إنشاء ورقة معلومات النظام فارغة.')
                    except Exception as e:
                        sync_details.append(f'فشل إنشاء ورقة معلومات النظام: {str(e)}')
            except LookupError as e:
                sync_details.append(f'نموذج معلومات الشركة غير متاح: {str(e)}')
            except Exception as e:
                sync_details.append(f'حدث خطأ أثناء مزامنة معلومات الشركة: {str(e)}')
        
        # مزامنة بيانات التواصل - استخدام النماذج المناسبة
        if config.sync_contact_details:
            try:
                # يمكن استخدام نموذج ContactInfo أو User حسب هيكل النظام
                ContactMethod = apps.get_model('customers', 'ContactMethod')
                contact_data = ContactMethod.objects.all()
                if contact_data.exists():
                    try:
                        count = sheets_service.sync_model_data(
                            spreadsheet_id=config.spreadsheet_id,
                            model_class=ContactMethod,
                            sheet_name='بيانات التواصل'
                        )
                        sync_details.append(f'تم مزامنة {count} من بيانات التواصل بنجاح.')
                        total_records += count
                    except Exception as e:
                        sync_details.append(f'فشل مزامنة بيانات التواصل: {str(e)}')
            except LookupError:
                try:
                    # محاولة استخدام نموذج User كبديل
                    User = apps.get_model('accounts', 'User')
                    user_data = User.objects.all()
                    if user_data.exists():
                        try:
                            count = sheets_service.sync_model_data(
                                spreadsheet_id=config.spreadsheet_id,
                                model_class=User,
                                sheet_name='بيانات المستخدمين'
                            )
                            sync_details.append(f'تم مزامنة {count} من بيانات المستخدمين بنجاح.')
                            total_records += count
                        except Exception as e:
                            sync_details.append(f'فشل مزامنة بيانات المستخدمين: {str(e)}')
                except LookupError:
                    sync_details.append('نماذج بيانات التواصل غير متاحة.')
        
        # مزامنة إعدادات النظام - استخدام أي نموذج للإعدادات
        if config.sync_system_settings:
            try:
                # محاولة استخدام نموذج SiteSettings إذا كان موجودًا
                SiteSettings = apps.get_model('accounts', 'SiteSettings')
                settings_data = SiteSettings.objects.all()
                if settings_data.exists():
                    try:
                        count = sheets_service.sync_model_data(
                            spreadsheet_id=config.spreadsheet_id,
                            model_class=SiteSettings,
                            sheet_name='إعدادات النظام'
                        )
                        sync_details.append(f'تم مزامنة {count} من إعدادات النظام بنجاح.')
                        total_records += count
                    except Exception as e:
                        sync_details.append(f'فشل مزامنة إعدادات النظام: {str(e)}')
            except LookupError:
                sync_details.append('نموذج إعدادات النظام غير متاح.')
        
        # مزامنة بيانات الفروع
        try:
            Branch = apps.get_model('accounts', 'Branch')
            branches_data = Branch.objects.all()
            if branches_data.exists():
                try:
                    count = sheets_service.sync_model_data(
                        spreadsheet_id=config.spreadsheet_id,
                        model_class=Branch,
                        sheet_name='الفروع'
                    )
                    sync_details.append(f'تم مزامنة {count} من بيانات الفروع بنجاح.')
                    total_records += count
                except Exception as e:
                    sync_details.append(f'فشل مزامنة بيانات الفروع: {str(e)}')
            else:
                try:
                    # إنشاء ورقة فارغة مع العناوين فقط إذا لم تكن هناك بيانات
                    headers = ['id', 'code', 'name', 'address', 'phone', 'email', 'is_main_branch', 'is_active']
                    data = [headers]
                    sheets_service.create_or_update_sheet(
                        spreadsheet_id=config.spreadsheet_id,
                        sheet_name='الفروع',
                        data=data
                    )
                    sync_details.append(f'تم إنشاء ورقة بيانات الفروع فارغة.')
                except Exception as e:
                    sync_details.append(f'فشل إنشاء ورقة بيانات الفروع: {str(e)}')
        except LookupError:
            sync_details.append('نموذج الفروع غير متاح.')
        
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
    
    # قائمة النماذج المتاحة للاستيراد - النماذج الأساسية فقط
    available_models = []
    
    # حصر النماذج الأساسية التي تم تحديدها من قبل المستخدم
    # 1. النماذج الرئيسية: العملاء، الطلبات، المعاينات، المنتجات، التركيبات
    if config.sync_customers:
        try:
            Customer = apps.get_model('customers', 'Customer')
            available_models.append(('customers.Customer', Customer._meta.verbose_name_plural))
        except LookupError:
            pass
        
    if config.sync_orders:
        try:
            Order = apps.get_model('orders', 'Order')
            available_models.append(('orders.Order', Order._meta.verbose_name_plural))
        except LookupError:
            pass
        
    if config.sync_products:
        try:
            Product = apps.get_model('inventory', 'Product')
            available_models.append(('inventory.Product', Product._meta.verbose_name_plural))
        except LookupError:
            pass
        
    if config.sync_inspections:
        try:
            Inspection = apps.get_model('inspections', 'Inspection')
            available_models.append(('inspections.Inspection', Inspection._meta.verbose_name_plural))
        except LookupError:
            pass
        
    if config.sync_installations:
        try:
            Installation = apps.get_model('installations', 'Installation')
            available_models.append(('installations.Installation', Installation._meta.verbose_name_plural))
        except LookupError:
            pass
    
    # 2. معلومات الشركة الأساسية
    if config.sync_company_info:
        try:
            CompanyInfo = apps.get_model('accounts', 'CompanyInfo')
            available_models.append(('accounts.CompanyInfo', 'معلومات الشركة'))
        except LookupError:
            pass
    
    # 3. بيانات الفروع
    try:
        Branch = apps.get_model('accounts', 'Branch')
        available_models.append(('accounts.Branch', 'الفروع'))
    except LookupError:
        pass
    
    # 4. بيانات المستخدمين
    try:
        User = apps.get_model('accounts', 'User')
        available_models.append(('accounts.User', 'بيانات المستخدمين'))
    except LookupError:
        pass
    
    if request.method == 'POST':
        form = GoogleSheetsImportForm(request.POST, model_choices=available_models)
        
        if form.is_valid():
            model_name = form.cleaned_data['model_choice']
            sheet_name = form.cleaned_data['sheet_name']
            replace_all = form.cleaned_data['replace_all']
            
            try:
                # الحصول على النموذج
                app_label, model_name = model_name.split('.')
                model_class = apps.get_model(app_label, model_name)
                
                # إنشاء خدمة المزامنة
                sheets_service = GoogleSheetsService(config.credentials_file)
                
                # استيراد البيانات مع استخدام خيار استبدال البيانات الموجودة
                count = sheets_service.import_data_from_sheet(
                    spreadsheet_id=config.spreadsheet_id,
                    sheet_name=sheet_name,
                    model_class=model_class,
                    replace_all=replace_all
                )
                
                # تسجيل الاستيراد
                details_msg = f'تم استيراد {count} سجل من {sheet_name} إلى {model_class._meta.verbose_name_plural}'
                if replace_all:
                    details_msg += ' (مع استبدال البيانات الموجودة)'
                
                SyncLog.objects.create(
                    status='success',
                    details=details_msg,
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
    else:
        form = GoogleSheetsImportForm(model_choices=available_models)
    
    context = {
        'form': form,
        'title': 'استيراد البيانات من Google Sheets',
    }
    
    return render(request, 'data_backup/import_from_sheets.html', context)

@user_passes_test(lambda u: u.is_staff)
def update_sync_interval(request):
    """تحديث فترة المزامنة التلقائية"""
    config = GoogleSheetsConfig.objects.first()
    if not config:
        messages.error(request, 'لم يتم تكوين إعدادات المزامنة بعد.')
        return redirect('data_backup:dashboard')
    
    if request.method == 'POST':
        form = SyncIntervalForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث فترة المزامنة بنجاح.')
            
            # إعادة تسجيل العملية في سجل المزامنة
            SyncLog.objects.create(
                status='success',
                details=f'تم تغيير فترة المزامنة التلقائية إلى {form.cleaned_data["sync_interval_minutes"]} دقيقة',
                records_synced=0,
                triggered_by=request.user
            )
            
            return redirect('data_backup:dashboard')
    else:
        form = SyncIntervalForm(instance=config)
    
    return render(request, 'data_backup/update_sync_interval.html', {
        'form': form,
        'config': config,
        'title': 'تعديل فترة المزامنة'
    })
