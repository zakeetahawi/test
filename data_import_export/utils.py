import os
import pandas as pd
import numpy as np
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.utils import timezone
from django.db import transaction
from django.utils.text import slugify

def generate_multi_sheet_template(model_names):
    """
    Generate a multi-sheet Excel template for importing data
    
    Args:
        model_names: List of model names in the format 'app_label.model_name'
        
    Returns:
        BytesIO object containing the Excel file
    """
    import io
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    # Create a BytesIO object to store the Excel file
    output = io.BytesIO()
    
    # Create a Pandas Excel writer using the BytesIO object
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Add an instructions sheet
        instructions_df = pd.DataFrame({
            'تعليمات الاستخدام': [
                'هذا الملف يحتوي على قوالب لاستيراد البيانات إلى نظام CRM الخواجة',
                'كل صفحة تمثل نوعًا مختلفًا من البيانات (المنتجات، العملاء، الطلبات، إلخ)',
                'قم بملء البيانات في كل صفحة وفقًا للأعمدة المحددة',
                'الحقول المميزة باللون الأحمر إلزامية ويجب ملؤها',
                'يمكنك استيراد الملف بالكامل من خلال اختيار "ملف متعدد الصفحات" في صفحة الاستيراد',
                'تأكد من عدم تغيير أسماء الصفحات أو الأعمدة لضمان نجاح الاستيراد'
            ]
        })
        instructions_df.to_excel(writer, sheet_name='_تعليمات', index=False)
        
        # Add a sheet for each model
        for model_name in model_names:
            app_label, model = model_name.split('.')
            
            # Get the model class
            model_class = apps.get_model(app_label, model)
            
            # Get the field names and required status
            fields = []
            required_fields = []
            field_verbose_names = {}
            
            for field in model_class._meta.fields:
                # Skip auto-generated fields
                if field.name in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']:
                    continue
                
                # Skip file fields
                if field.get_internal_type() == 'FileField' or field.get_internal_type() == 'ImageField':
                    continue
                
                fields.append(field.name)
                field_verbose_names[field.name] = field.verbose_name
                
                # Check if field is required
                if not field.blank and not field.null and not field.has_default():
                    required_fields.append(field.name)
            
            # Create a sample dataframe with example data
            sample_data = {}
            example_row = {}
            
            # Add example data based on model type
            if model == 'product':
                example_row = {
                    'name': 'منتج نموذجي',
                    'sku': 'SKU12345',
                    'description': 'وصف المنتج النموذجي',
                    'price': 100.00,
                    'cost': 70.00,
                    'stock': 50,
                }
            elif model == 'customer':
                example_row = {
                    'name': 'عميل نموذجي',
                    'phone': '01234567890',
                    'email': 'customer@example.com',
                    'address': 'عنوان العميل النموذجي',
                }
            elif model == 'supplier':
                example_row = {
                    'name': 'مورد نموذجي',
                    'phone': '01234567890',
                    'email': 'supplier@example.com',
                    'address': 'عنوان المورد النموذجي',
                }
            elif model == 'order':
                example_row = {
                    'order_number': 'ORD12345',
                    'customer_id': 1,
                    'total': 500.00,
                    'status': 'pending',
                }
            
            # Create the dataframe with field names as columns
            for field in fields:
                # Use example data if available, otherwise empty string
                if field in example_row:
                    sample_data[field] = [example_row[field], '']
                else:
                    sample_data[field] = ['', '']
                    
            # Create DataFrame with verbose field names
            verbose_columns = [field_verbose_names.get(field, field) for field in fields]
            df = pd.DataFrame(sample_data)
            
            # Get the Arabic name for the sheet
            sheet_name = model
            if model == 'product':
                sheet_name = 'المنتجات'
            elif model == 'customer':
                sheet_name = 'العملاء'
            elif model == 'supplier':
                sheet_name = 'الموردين'
            elif model == 'order':
                sheet_name = 'الطلبات'
            elif model == 'category':
                sheet_name = 'فئات المنتجات'
            elif model == 'customercategory':
                sheet_name = 'فئات العملاء'
            elif model == 'orderitem':
                sheet_name = 'عناصر الطلبات'
            elif model == 'payment':
                sheet_name = 'المدفوعات'
            
            # Write the dataframe to the Excel file
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=fields)
            
            # Get the worksheet
            worksheet = writer.sheets[sheet_name]
            
            # Add instructions as a header row
            instructions = f"قم بملء البيانات أدناه لاستيراد {model_class._meta.verbose_name_plural}"
            worksheet['A1'] = instructions
            
            # Add column descriptions as headers
            for i, field in enumerate(fields):
                field_obj = model_class._meta.get_field(field)
                description = str(field_obj.verbose_name)
                col_letter = chr(65 + i)  # A, B, C, etc.
                worksheet[f'{col_letter}2'] = description
    
    # Reset the pointer to the beginning of the BytesIO object
    output.seek(0)
    
    return output

def process_multi_sheet_import(file_path, import_log, new_only=False, chunk_size=1000):
    """
    معالجة ملف Excel متعدد الصفحات للاستيراد
    """
    import pandas as pd
    from django.apps import apps
    
    success_count = 0
    error_count = 0
    error_details = []
    
    try:
        # قراءة جميع الصفحات
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        for sheet_name in sheet_names:
            try:
                # قراءة البيانات على دفعات
                for chunk in pd.read_excel(excel_file, sheet_name=sheet_name, chunksize=chunk_size):
                    # تحديد النموذج بناءً على اسم الصفحة
                    model_name = sheet_name.lower()
                    try:
                        if model_name == 'products':
                            app_label, model = 'inventory', 'product'
                        elif model_name == 'suppliers':
                            app_label, model = 'inventory', 'supplier'
                        elif model_name == 'customers':
                            app_label, model = 'customers', 'customer'
                        elif model_name == 'orders':
                            app_label, model = 'orders', 'order'
                        else:
                            continue
                        
                        model_class = apps.get_model(app_label, model)
                        
                        # معالجة الدفعة
                        chunk_success, chunk_error, chunk_details = process_dataframe(
                            chunk,
                            model,
                            model_class,
                            new_only=new_only
                        )
                        
                        success_count += chunk_success
                        error_count += chunk_error
                        if chunk_details:
                            error_details.append(f"Sheet {sheet_name}:\n{chunk_details}")
                            
                    except Exception as e:
                        error_details.append(f"Error processing sheet {sheet_name}: {str(e)}")
                        continue
                        
            except Exception as e:
                error_details.append(f"Error reading sheet {sheet_name}: {str(e)}")
                continue
                
    except Exception as e:
        error_details.append(f"Error reading Excel file: {str(e)}")
    
    return success_count, error_count, error_details

def validate_data(data, model_class):
    """
    التحقق من صحة البيانات قبل الاستيراد
    """
    errors = []
    
    # التحقق من الحقول المطلوبة
    required_fields = [f.name for f in model_class._meta.fields if not f.blank and not f.null 
                      and f.name not in ['id', 'created_at', 'updated_at']]
    
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        errors.append(f"Missing required fields: {', '.join(missing_fields)}")
    
    # التحقق من صحة أنواع البيانات
    for field_name, value in data.items():
        try:
            field = model_class._meta.get_field(field_name)
            
            # التحقق من نوع البيانات
            if value is not None:
                if field.get_internal_type() in ['IntegerField', 'PositiveIntegerField']:
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"Invalid integer value for field {field_name}: {value}")
                
                elif field.get_internal_type() in ['DecimalField', 'FloatField']:
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"Invalid numeric value for field {field_name}: {value}")
                
                elif field.get_internal_type() == 'DateField':
                    try:
                        pd.to_datetime(value)
                    except (ValueError, TypeError):
                        errors.append(f"Invalid date value for field {field_name}: {value}")
                
                elif field.get_internal_type() == 'BooleanField':
                    if not isinstance(value, bool) and str(value).lower() not in ['true', 'false', '0', '1']:
                        errors.append(f"Invalid boolean value for field {field_name}: {value}")
        
        except Exception as e:
            errors.append(f"Error validating field {field_name}: {str(e)}")
    
    return errors

def generate_multi_sheet_export(model_names, chunk_size=1000):
    """
    إنشاء ملف Excel متعدد الصفحات للتصدير
    """
    import pandas as pd
    import io
    from django.apps import apps
    
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for model_name in model_names:
                try:
                    # الحصول على النموذج
                    app_label, model = model_name.split('.')
                    model_class = apps.get_model(app_label, model)
                    
                    # استخراج البيانات على دفعات
                    data = []
                    for instance in model_class.objects.iterator(chunk_size=chunk_size):
                        item = {}
                        for field in model_class._meta.fields:
                            field_name = field.name
                            field_value = getattr(instance, field_name)
                            
                            # معالجة العلاقات
                            if field.is_relation:
                                if field_value is not None:
                                    field_value = str(field_value)
                                else:
                                    field_value = None
                            
                            item[field_name] = field_value
                        
                        data.append(item)
                    
                    # إنشاء DataFrame وحفظه في الملف
                    if data:
                        df = pd.DataFrame(data)
                        sheet_name = model.capitalize()[:31]  # Excel يقبل فقط 31 حرف كحد أقصى
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                except Exception as e:
                    print(f"Error exporting {model_name}: {str(e)}")
                    continue
        
        output.seek(0)
        return output
    
    except Exception as e:
        print(f"Error generating Excel file: {str(e)}")
        return None

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
