import os
import pandas as pd
import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.core.paginator import Paginator
from django.utils.text import slugify

from .models import ImportExportLog, ImportTemplate
from .forms import ImportForm, ExportForm, ImportTemplateForm

@staff_member_required
def import_export_dashboard(request):
    """
    Dashboard for import/export operations
    """
    # Get recent import/export logs
    recent_logs = ImportExportLog.objects.all()[:10]
    
    # Get import templates
    templates = ImportTemplate.objects.filter(is_active=True)
    
    context = {
        'recent_logs': recent_logs,
        'templates': templates,
        'title': 'استيراد وتصدير البيانات',
    }
    
    return render(request, 'data_import_export/dashboard.html', context)

@staff_member_required
def import_data(request):
    """
    View for importing data
    """
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                
                # التحقق من حجم الملف (الحد الأقصى 50 ميجابايت)
                if file.size > 50 * 1024 * 1024:  # 50MB
                    messages.error(request, 'حجم الملف كبير جداً. الحد الأقصى المسموح به هو 50 ميجابايت.')
                    return redirect('data_import_export:import_data')

                # التحقق من نوع الملف
                file_ext = os.path.splitext(file.name)[1].lower()
                if file_ext not in ['.xlsx', '.csv', '.json']:
                    messages.error(request, 'نوع الملف غير مدعوم. الأنواع المدعومة هي: XLSX, CSV, JSON')
                    return redirect('data_import_export:import_data')

                # إنشاء سجل الاستيراد
                import_log = form.save(commit=False)
                import_log.operation_type = 'import'
                import_log.file_name = file.name
                import_log.status = 'processing'
                import_log.created_by = request.user
                
                # التحقق من استيراد متعدد الصفحات
                is_multi_sheet = form.cleaned_data.get('is_multi_sheet', False)
                model_name = form.cleaned_data['model_name']
                import_log.is_multi_sheet = is_multi_sheet or model_name == 'multi_sheet'
                
                # التحقق من استيراد السجلات الجديدة فقط
                new_only = form.cleaned_data.get('new_only', False)
                import_log.details = 'استيراد البيانات الجديدة فقط' if new_only else 'استيراد وتحديث البيانات'

                # تحديد نوع النموذج
                if model_name == 'multi_sheet':
                    import_log.model_name = 'inventory.product'  # قيمة مؤقتة
                else:
                    import_log.model_name = model_name
                
                import_log.save()

                # معالجة الملف بناءً على نوعه
                if file_ext == '.xlsx':
                    if import_log.is_multi_sheet:
                        success_count, error_count, error_details = process_multi_sheet_import(
                            import_log.file.path, 
                            import_log, 
                            new_only=new_only,
                            chunk_size=1000  # معالجة البيانات على دفعات
                        )
                    else:
                        df = pd.read_excel(file, chunksize=1000)  # قراءة البيانات على دفعات
                        success_count = error_count = 0
                        error_details = []
                        
                        for chunk in df:
                            chunk_success, chunk_error, chunk_details = process_dataframe(
                                chunk,
                                model_name.split('.')[1],
                                apps.get_model(*model_name.split('.')),
                                new_only=new_only
                            )
                            success_count += chunk_success
                            error_count += chunk_error
                            error_details.extend(chunk_details if isinstance(chunk_details, list) else [chunk_details])

                elif file_ext == '.csv':
                    for chunk in pd.read_csv(file, chunksize=1000):
                        chunk_success, chunk_error, chunk_details = process_dataframe(
                            chunk,
                            model_name.split('.')[1],
                            apps.get_model(*model_name.split('.')),
                            new_only=new_only
                        )
                        success_count += chunk_success
                        error_count += chunk_error
                        error_details.extend(chunk_details if isinstance(chunk_details, list) else [chunk_details])

                elif file_ext == '.json':
                    data = json.load(file)
                    # معالجة البيانات على دفعات
                    chunk_size = 1000
                    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
                    
                    success_count = error_count = 0
                    error_details = []
                    
                    for chunk in chunks:
                        df = pd.DataFrame(chunk)
                        chunk_success, chunk_error, chunk_details = process_dataframe(
                            df,
                            model_name.split('.')[1],
                            apps.get_model(*model_name.split('.')),
                            new_only=new_only
                        )
                        success_count += chunk_success
                        error_count += chunk_error
                        error_details.extend(chunk_details if isinstance(chunk_details, list) else [chunk_details])

                # تحديث سجل الاستيراد
                total_records = success_count + error_count
                import_log.records_count = total_records
                import_log.success_count = success_count
                import_log.error_count = error_count
                import_log.error_details = '\n'.join(error_details) if error_details else ''
                import_log.status = 'completed' if error_count == 0 else 'completed_with_errors'
                import_log.completed_at = timezone.now()
                import_log.save()

                # إظهار رسائل النجاح والأخطاء
                messages.success(request, f'تم استيراد {success_count} من {total_records} سجل بنجاح.')
                if error_count > 0:
                    messages.warning(request, f'فشل استيراد {error_count} سجل. يمكنك مراجعة التفاصيل في سجل الاستيراد.')

                return redirect('data_import_export:import_log_detail', pk=import_log.pk)

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء استيراد البيانات: {str(e)}')
                if 'import_log' in locals():
                    import_log.status = 'failed'
                    import_log.error_details = str(e)
                    import_log.completed_at = timezone.now()
                    import_log.save()
                    return redirect('data_import_export:import_log_detail', pk=import_log.pk)

    else:
        form = ImportForm()

    templates = ImportTemplate.objects.filter(is_active=True)
    context = {
        'form': form,
        'templates': templates,
        'title': 'استيراد البيانات',
    }
    
    return render(request, 'data_import_export/import_form.html', context)

def process_dataframe(df, model, model_class, new_only=False):
    """
    Process a dataframe for importing data
    
    Args:
        df: Pandas DataFrame
        model: Model name
        model_class: Model class
        new_only: Boolean indicating whether to import only new records
        
    Returns:
        Tuple of (records_count, success_count, error_count, error_details)
    """
    from .utils import (
        handle_product_import, handle_supplier_import, 
        handle_customer_import, handle_order_import
    )
    
    records_count = len(df)
    success_count = 0
    error_count = 0
    error_details = []
    
    # Process each row
    with transaction.atomic():
        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if row.isnull().all():
                    continue
                
                # Convert row to dict and remove NaN values
                row_dict = {}
                for key, value in row.to_dict().items():
                    if pd.notna(value):
                        row_dict[key] = value
                
                # Skip rows with no data
                if not row_dict:
                    continue
                
                # Handle specific model import logic
                if model == 'product':
                    # Handle product import
                    instance = handle_product_import(row_dict, new_only=new_only)
                elif model == 'supplier':
                    # Handle supplier import
                    instance = handle_supplier_import(row_dict, new_only=new_only)
                elif model == 'customer':
                    # Handle customer import
                    instance = handle_customer_import(row_dict, new_only=new_only)
                elif model == 'order':
                    # Handle order import
                    instance = handle_order_import(row_dict, new_only=new_only)
                else:
                    # Generic import
                    if new_only:
                        if not model_class.objects.filter(**row_dict).exists():
                            instance = model_class.objects.create(**row_dict)
                    else:
                        instance = model_class.objects.create(**row_dict)
                
                success_count += 1
            except Exception as e:
                error_count += 1
                error_details.append(f"Row {index+1}: {str(e)}")
    
    return records_count, success_count, error_count, '\n'.join(error_details)

@staff_member_required
def export_data(request):
    """
    View for exporting data
    """
    if request.method == 'POST':
        form = ExportForm(request.POST)
        if form.is_valid():
            try:
                # Get form data
                model_name = form.cleaned_data['model_name']
                export_format = form.cleaned_data['export_format']
                date_range = form.cleaned_data.get('date_range', 'all')
                
                # Get the model class
                app_label, model = model_name.split('.')
                model_class = apps.get_model(app_label, model)
                
                # Filter queryset based on date range if applicable
                queryset = model_class.objects.all()
                if hasattr(model_class, 'created_at') and date_range != 'all':
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    now = timezone.now()
                    if date_range == 'today':
                        queryset = queryset.filter(created_at__date=now.date())
                    elif date_range == 'week':
                        queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
                    elif date_range == 'month':
                        queryset = queryset.filter(created_at__gte=now - timedelta(days=30))
                    elif date_range == 'year':
                        queryset = queryset.filter(created_at__year=now.year)
                
                # Create export log
                export_log = ImportExportLog.objects.create(
                    operation_type='export',
                    model_name=model_name,
                    file_name=f"{model}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{export_format}",
                    status='processing',
                    records_count=queryset.count(),
                    created_by=request.user
                )
                
                try:
                    # Handle multi-sheet export if requested
                    if export_format == 'xlsx' and form.cleaned_data.get('multi_sheet', True):
                        # Get related models
                        if model_name == 'multi_sheet':
                            related_models = [
                                'inventory.product',
                                'inventory.supplier',
                                'inventory.category',
                                'customers.customer',
                                'customers.customercategory',
                                'orders.order',
                                'orders.orderitem',
                                'orders.payment'
                            ]
                        else:
                            related_models = [model_name]
                            
                            # Add related models based on the main model
                            if model == 'product':
                                related_models.extend([
                                    'inventory.category',
                                    'inventory.supplier',
                                    'inventory.stocktransaction'
                                ])
                            elif model == 'customer':
                                related_models.extend([
                                    'customers.customercategory',
                                    'customers.customercontact',
                                    'orders.order'
                                ])
                            elif model == 'order':
                                related_models.extend([
                                    'orders.orderitem',
                                    'orders.payment'
                                ])
                        
                        # Generate multi-sheet export
                        from .utils import generate_multi_sheet_export
                        output = generate_multi_sheet_export(related_models, chunk_size=1000)
                        
                        if output:
                            response = HttpResponse(
                                output.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                            response['Content-Disposition'] = f'attachment; filename="{export_log.file_name}"'
                        else:
                            raise Exception('فشل إنشاء ملف Excel')
                    
                    else:
                        # Convert queryset to DataFrame
                        data = []
                        # Process in chunks to handle large datasets
                        chunk_size = 1000
                        for instance in queryset.iterator(chunk_size=chunk_size):
                            item = {}
                            for field in model_class._meta.fields:
                                if field.name in ['created_at', 'updated_at', 'file']:
                                    continue
                                    
                                field_name = field.name
                                field_value = getattr(instance, field_name)
                                
                                # Handle foreign keys and dates
                                if field.is_relation:
                                    if field_value is not None:
                                        if hasattr(field_value, 'name'):
                                            field_value = field_value.name
                                        else:
                                            field_value = str(field_value)
                                elif isinstance(field_value, (datetime.date, datetime.datetime)):
                                    field_value = field_value.strftime('%Y-%m-%d %H:%M:%S')
                                
                                item[field.verbose_name or field_name] = field_value
                            
                            data.append(item)
                        
                        df = pd.DataFrame(data)
                        
                        # Create response based on export format
                        if export_format == 'xlsx':
                            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                            response['Content-Disposition'] = f'attachment; filename="{export_log.file_name}"'
                            df.to_excel(response, index=False, sheet_name=model_class._meta.verbose_name_plural[:31])
                            
                        elif export_format == 'csv':
                            response = HttpResponse(content_type='text/csv')
                            response['Content-Disposition'] = f'attachment; filename="{export_log.file_name}"'
                            df.to_csv(response, index=False, encoding='utf-8-sig')  # Use UTF-8 with BOM for Excel compatibility
                            
                        elif export_format == 'json':
                            response = HttpResponse(content_type='application/json')
                            response['Content-Disposition'] = f'attachment; filename="{export_log.file_name}"'
                            df.to_json(response, orient='records', force_ascii=False)
                    
                    # Update export log
                    export_log.status = 'completed'
                    export_log.success_count = queryset.count()
                    export_log.completed_at = timezone.now()
                    export_log.save()
                    
                    return response
                
                except Exception as e:
                    export_log.status = 'failed'
                    export_log.error_details = str(e)
                    export_log.completed_at = timezone.now()
                    export_log.save()
                    
                    messages.error(request, f'فشل تصدير البيانات: {str(e)}')
            
            except Exception as e:
                messages.error(request, f'فشل تصدير البيانات: {str(e)}')
    
    else:
        form = ExportForm()
    
    context = {
        'form': form,
        'title': 'تصدير البيانات',
    }
    
    return render(request, 'data_import_export/export_form.html', context)

@staff_member_required
def import_log_list(request):
    """
    View for listing import/export logs
    """
    # Get filter parameters
    operation_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    # Filter logs
    logs = ImportExportLog.objects.all()
    
    if operation_type:
        logs = logs.filter(operation_type=operation_type)
    
    if status:
        logs = logs.filter(status=status)
    
    # Paginate logs
    paginator = Paginator(logs, 10)  # Show 10 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'operation_type': operation_type,
        'status': status,
        'title': 'سجلات الاستيراد والتصدير',
    }
    
    return render(request, 'data_import_export/import_log_list.html', context)

@staff_member_required
def import_log_detail(request, pk):
    """
    View for import/export log detail
    """
    log = get_object_or_404(ImportExportLog, pk=pk)
    
    context = {
        'log': log,
        'title': f"تفاصيل {log.get_operation_type_display()}",
    }
    
    return render(request, 'data_import_export/import_log_detail.html', context)

@staff_member_required
def import_template_list(request):
    """
    View for listing import templates
    """
    templates = ImportTemplate.objects.all()
    
    context = {
        'templates': templates,
        'title': 'قوالب الاستيراد',
    }
    
    return render(request, 'data_import_export/import_template_list.html', context)

@staff_member_required
def import_template_create(request):
    """
    View for creating import template
    """
    if request.method == 'POST':
        form = ImportTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إنشاء قالب الاستيراد بنجاح.')
            return redirect('data_import_export:import_template_list')
    else:
        form = ImportTemplateForm()
    
    context = {
        'form': form,
        'title': 'إنشاء قالب استيراد',
    }
    
    return render(request, 'data_import_export/import_template_form.html', context)

@staff_member_required
def import_template_update(request, pk):
    """
    View for updating import template
    """
    template = get_object_or_404(ImportTemplate, pk=pk)
    
    if request.method == 'POST':
        form = ImportTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث قالب الاستيراد بنجاح.')
            return redirect('data_import_export:import_template_list')
    else:
        form = ImportTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'title': 'تعديل قالب استيراد',
    }
    
    return render(request, 'data_import_export/import_template_form.html', context)

@staff_member_required
def import_template_delete(request, pk):
    """
    View for deleting import template
    """
    template = get_object_or_404(ImportTemplate, pk=pk)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'تم حذف قالب الاستيراد بنجاح.')
        return redirect('data_import_export:import_template_list')
    
    context = {
        'template': template,
        'title': 'حذف قالب استيراد',
    }
    
    return render(request, 'data_import_export/import_template_confirm_delete.html', context)

@staff_member_required
def download_import_template(request, pk):
    """
    View for downloading import template
    """
    template = get_object_or_404(ImportTemplate, pk=pk)
    
    # Get the file
    file_path = template.file.path
    
    # Create response
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{template.file.name.split("/")[-1]}"'
    
    return response

# Helper functions for importing specific models

def handle_product_import(data, new_only=False):
    """
    Handle product import
    """
    from inventory.models import Product, Category
    
    # Get or create category
    category = None
    if 'category' in data and data['category']:
        category, created = Category.objects.get_or_create(name=data['category'])
    
    # Create or update product
    if 'code' in data and data['code']:
        if new_only:
            product = Product.objects.filter(code=data['code']).first()
            if not product:
                product = Product.objects.create(
                    code=data['code'],
                    name=data.get('name', ''),
                    description=data.get('description', ''),
                    unit=data.get('unit', 'piece'),
                    price=data.get('price', 0),
                    minimum_stock=data.get('minimum_stock', 0),
                    category=category,
                )
        else:
            product, created = Product.objects.update_or_create(
                code=data['code'],
                defaults={
                    'name': data.get('name', ''),
                    'description': data.get('description', ''),
                    'unit': data.get('unit', 'piece'),
                    'price': data.get('price', 0),
                    'minimum_stock': data.get('minimum_stock', 0),
                    'category': category,
                }
            )
    else:
        product = Product.objects.create(
            name=data.get('name', ''),
            code=slugify(data.get('name', '')),
            description=data.get('description', ''),
            unit=data.get('unit', 'piece'),
            price=data.get('price', 0),
            minimum_stock=data.get('minimum_stock', 0),
            category=category,
        )
    
    return product

def handle_supplier_import(data, new_only=False):
    """
    Handle supplier import
    """
    from inventory.models import Supplier
    
    # Create or update supplier
    if 'name' in data and data['name']:
        if new_only:
            supplier = Supplier.objects.filter(name=data['name']).first()
            if not supplier:
                supplier = Supplier.objects.create(
                    name=data['name'],
                    contact_person=data.get('contact_person', ''),
                    phone=data.get('phone', ''),
                    email=data.get('email', ''),
                    address=data.get('address', ''),
                    tax_number=data.get('tax_number', ''),
                    notes=data.get('notes', ''),
                )
        else:
            supplier, created = Supplier.objects.update_or_create(
                name=data['name'],
                defaults={
                    'contact_person': data.get('contact_person', ''),
                    'phone': data.get('phone', ''),
                    'email': data.get('email', ''),
                    'address': data.get('address', ''),
                    'tax_number': data.get('tax_number', ''),
                    'notes': data.get('notes', ''),
                }
            )
    else:
        raise ValueError('Supplier name is required')
    
    return supplier

def handle_customer_import(data, new_only=False):
    """
    Handle customer import
    """
    from customers.models import Customer, CustomerCategory
    from accounts.models import Branch
    
    # Get or create category
    category = None
    if 'category' in data and data['category']:
        category, created = CustomerCategory.objects.get_or_create(name=data['category'])
    
    # Get branch
    branch = None
    if 'branch' in data and data['branch']:
        try:
            branch = Branch.objects.get(code=data['branch'])
        except Branch.DoesNotExist:
            branch = Branch.objects.first()
    else:
        branch = Branch.objects.first()
    
    # Create or update customer
    if 'code' in data and data['code']:
        if new_only:
            customer = Customer.objects.filter(code=data['code']).first()
            if not customer:
                customer = Customer.objects.create(
                    code=data['code'],
                    name=data.get('name', ''),
                    phone=data.get('phone', ''),
                    email=data.get('email', ''),
                    address=data.get('address', ''),
                    customer_type=data.get('customer_type', 'individual'),
                    category=category,
                    branch=branch,
                )
        else:
            customer, created = Customer.objects.update_or_create(
                code=data['code'],
                defaults={
                    'name': data.get('name', ''),
                    'phone': data.get('phone', ''),
                    'email': data.get('email', ''),
                    'address': data.get('address', ''),
                    'customer_type': data.get('customer_type', 'individual'),
                    'category': category,
                    'branch': branch,
                }
            )
    else:
        customer = Customer.objects.create(
            name=data.get('name', ''),
            code=f"C{Customer.objects.count() + 1:04d}",
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            address=data.get('address', ''),
            customer_type=data.get('customer_type', 'individual'),
            category=category,
            branch=branch,
        )
    
    return customer

def handle_order_import(data, new_only=False):
    """
    Handle order import
    """
    from orders.models import Order
    from customers.models import Customer
    from accounts.models import User
    
    # Get customer
    customer = None
    if 'customer' in data and data['customer']:
        try:
            customer = Customer.objects.get(name=data['customer'])
        except Customer.DoesNotExist:
            customer = Customer.objects.first()
    else:
        customer = Customer.objects.first()
    
    # Get user
    user = None
    if 'created_by' in data and data['created_by']:
        try:
            user = User.objects.get(username=data['created_by'])
        except User.DoesNotExist:
            user = User.objects.filter(is_staff=True).first()
    else:
        user = User.objects.filter(is_staff=True).first()
    
    # Create or update order
    if 'order_number' in data and data['order_number']:
        if new_only:
            order = Order.objects.filter(order_number=data['order_number']).first()
            if not order:
                order = Order.objects.create(
                    order_number=data['order_number'],
                    customer=customer,
                    delivery_date=data.get('delivery_date'),
                    status=data.get('status', 'pending'),
                    notes=data.get('notes', ''),
                    created_by=user,
                )
        else:
            order, created = Order.objects.update_or_create(
                order_number=data['order_number'],
                defaults={
                    'customer': customer,
                    'delivery_date': data.get('delivery_date'),
                    'status': data.get('status', 'pending'),
                    'notes': data.get('notes', ''),
                    'created_by': user,
                }
            )
    else:
        order = Order.objects.create(
            customer=customer,
            order_number=f"ORD{Order.objects.count() + 1:04d}",
            delivery_date=data.get('delivery_date'),
            status=data.get('status', 'pending'),
            notes=data.get('notes', ''),
            created_by=user,
        )
    
    return order
