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
            # Create import log
            import_log = form.save(commit=False)
            import_log.operation_type = 'import'
            import_log.file_name = request.FILES['file'].name
            import_log.status = 'processing'
            import_log.created_by = request.user
            
            # Check if it's a multi-sheet import
            is_multi_sheet = form.cleaned_data.get('is_multi_sheet', False)
            model_name = form.cleaned_data['model_name']
            import_log.is_multi_sheet = is_multi_sheet or model_name == 'multi_sheet'
            
            # If model_name is 'multi_sheet', set it to a default value temporarily
            # It will be determined automatically during processing
            if model_name == 'multi_sheet':
                import_log.model_name = 'inventory.product'  # Temporary value
            else:
                import_log.model_name = model_name
                
            import_log.save()
            
            try:
                # Process the file
                file_path = import_log.file.path
                file_ext = os.path.splitext(file_path)[1].lower()
                
                # Handle multi-sheet Excel file
                if file_ext == '.xlsx' and import_log.is_multi_sheet:
                    # Process multi-sheet Excel file
                    from .utils import process_multi_sheet_import
                    success_count, error_count, error_details_list = process_multi_sheet_import(file_path, import_log)
                    error_details = '\n'.join(error_details_list)
                    records_count = success_count + error_count
                    
                    # Update import log
                    import_log.records_count = records_count
                    import_log.success_count = success_count
                    import_log.error_count = error_count
                    import_log.error_details = error_details
                    import_log.status = 'completed' if error_count == 0 else 'failed'
                    import_log.completed_at = timezone.now()
                    import_log.save()
                    
                    messages.success(request, f'تم استيراد {success_count} من {records_count} سجل بنجاح من ملف متعدد الصفحات.')
                    if error_count > 0:
                        messages.warning(request, f'فشل استيراد {error_count} سجل. راجع سجل الاستيراد للتفاصيل.')
                    
                    return redirect('data_import_export:import_log_detail', pk=import_log.pk)
                
                # Handle single-model import
                model_name = import_log.model_name
                app_label, model = model_name.split('.')
                
                # Get the model class
                model_class = apps.get_model(app_label, model)
                content_type = ContentType.objects.get_for_model(model_class)
                import_log.content_type = content_type
                import_log.save()
                
                # Process the file based on its extension
                if file_ext == '.xlsx':
                    # Process Excel file
                    df = pd.read_excel(file_path)
                    records_count, success_count, error_count, error_details = process_dataframe(df, model, model_class)
                elif file_ext == '.csv':
                    df = pd.read_csv(file_path)
                    records_count, success_count, error_count, error_details = process_dataframe(df, model, model_class)
                elif file_ext == '.json':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    df = pd.DataFrame(data)
                    records_count, success_count, error_count, error_details = process_dataframe(df, model, model_class)
                else:
                    raise ValueError(f"صيغة الملف غير مدعومة: {file_ext}")
                
                # Update import log
                import_log.records_count = records_count
                import_log.success_count = success_count
                import_log.error_count = error_count
                import_log.error_details = error_details
                import_log.status = 'completed' if error_count == 0 else 'failed'
                import_log.completed_at = timezone.now()
                import_log.save()
                
                messages.success(request, f'تم استيراد {success_count} من {records_count} سجل بنجاح.')
                if error_count > 0:
                    messages.warning(request, f'فشل استيراد {error_count} سجل. راجع سجل الاستيراد للتفاصيل.')
                
                return redirect('data_import_export:import_log_detail', pk=import_log.pk)
            
            except Exception as e:
                import_log.status = 'failed'
                import_log.error_details = str(e)
                import_log.completed_at = timezone.now()
                import_log.save()
                
                messages.error(request, f'فشل استيراد البيانات: {str(e)}')
    else:
        form = ImportForm()
    
    # Get import templates
    templates = ImportTemplate.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'templates': templates,
        'title': 'استيراد البيانات',
    }
    
    return render(request, 'data_import_export/import_form.html', context)

def process_dataframe(df, model, model_class):
    """
    Process a dataframe for importing data
    
    Args:
        df: Pandas DataFrame
        model: Model name
        model_class: Model class
        
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
                    instance = handle_product_import(row_dict)
                elif model == 'supplier':
                    # Handle supplier import
                    instance = handle_supplier_import(row_dict)
                elif model == 'customer':
                    # Handle customer import
                    instance = handle_customer_import(row_dict)
                elif model == 'order':
                    # Handle order import
                    instance = handle_order_import(row_dict)
                else:
                    # Generic import
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
            # Get form data
            model_name = form.cleaned_data['model_name']
            export_format = form.cleaned_data['export_format']
            
            # Get the model class
            app_label, model = model_name.split('.')
            model_class = apps.get_model(app_label, model)
            
            # Get all records
            queryset = model_class.objects.all()
            
            # Create export log
            export_log = ImportExportLog(
                operation_type='export',
                model_name=model_name,
                file_name=f"{model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}",
                status='processing',
                records_count=queryset.count(),
                created_by=request.user
            )
            
            try:
                # Convert queryset to DataFrame
                data = []
                for obj in queryset:
                    # Convert model instance to dict
                    item = {}
                    for field in model_class._meta.fields:
                        field_name = field.name
                        field_value = getattr(obj, field_name)
                        
                        # Handle foreign keys
                        if field.is_relation:
                            if field_value is not None:
                                field_value = str(field_value)
                            else:
                                field_value = None
                        
                        item[field_name] = field_value
                    
                    data.append(item)
                
                df = pd.DataFrame(data)
                
                # Check if multi-sheet export is requested
                if export_format == 'xlsx' and form.cleaned_data.get('multi_sheet', True):
                    # Get related models based on the selected model
                    app_label = model_name.split('.')[0]
                    related_models = []
                    
                    # Define comprehensive model relationships for each app
                    if app_label == 'inventory':
                        related_models = [
                            'inventory.product', 
                            'inventory.supplier', 
                            'inventory.category',
                            'inventory.stocktransaction',
                            'inventory.purchaseorder'
                        ]
                    elif app_label == 'customers':
                        related_models = [
                            'customers.customer', 
                            'customers.customercategory',
                            'customers.customercontact'
                        ]
                    elif app_label == 'orders':
                        related_models = [
                            'orders.order', 
                            'orders.orderitem', 
                            'orders.payment'
                        ]
                    elif model_name == 'multi_sheet':
                        # Export all main models if multi-sheet option is selected
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
                    
                    # Generate multi-sheet Excel file
                    from .utils import generate_multi_sheet_export
                    output = generate_multi_sheet_export(related_models)
                    
                    # Create response
                    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = f'attachment; filename="{export_log.file_name}"'
                else:
                    # Create response based on export format
                    if export_format == 'xlsx':
                        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                        response['Content-Disposition'] = f'attachment; filename="{export_log.file_name}"'
                        df.to_excel(response, index=False)
                        
                    elif export_format == 'csv':
                        response = HttpResponse(content_type='text/csv')
                        response['Content-Disposition'] = f'attachment; filename="{export_log.file_name}"'
                        df.to_csv(response, index=False)
                        
                    elif export_format == 'json':
                        response = HttpResponse(content_type='application/json')
                        response['Content-Disposition'] = f'attachment; filename="{export_log.file_name}"'
                        df.to_json(response, orient='records')
                
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

def handle_product_import(data):
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

def handle_supplier_import(data):
    """
    Handle supplier import
    """
    from inventory.models import Supplier
    
    # Create or update supplier
    if 'name' in data and data['name']:
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

def handle_customer_import(data):
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

def handle_order_import(data):
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
