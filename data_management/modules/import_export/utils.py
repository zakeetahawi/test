"""
أدوات وحدة استيراد وتصدير البيانات
"""

import pandas as pd
import openpyxl
import json
import os
import tempfile
from django.apps import apps
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

def get_model_from_string(model_string):
    """
    الحصول على نموذج من سلسلة نصية
    
    Args:
        model_string: سلسلة نصية تمثل النموذج (مثال: 'app_name.ModelName')
        
    Returns:
        نموذج Django
    """
    try:
        app_label, model_name = model_string.split('.')
        return apps.get_model(app_label, model_name)
    except (ValueError, LookupError):
        raise ValueError(f"النموذج '{model_string}' غير موجود")

def process_import_file(file, model_string):
    """
    معالجة ملف الاستيراد
    
    Args:
        file: ملف الاستيراد
        model_string: سلسلة نصية تمثل النموذج
        
    Returns:
        قاموس يحتوي على نتائج الاستيراد
    """
    # الحصول على النموذج
    model = get_model_from_string(model_string)
    
    # تحديد نوع الملف
    file_ext = os.path.splitext(file.name)[1].lower()
    
    # قراءة البيانات من الملف
    if file_ext == '.xlsx' or file_ext == '.xls':
        df = pd.read_excel(file)
    elif file_ext == '.csv':
        df = pd.read_csv(file)
    elif file_ext == '.json':
        data = json.load(file)
        return process_json_import(data, model)
    else:
        raise ValueError(f"نوع الملف '{file_ext}' غير مدعوم")
    
    # تحويل DataFrame إلى قائمة من القواميس
    records = df.to_dict('records')
    
    # استيراد البيانات
    return process_records_import(records, model)

def process_records_import(records, model):
    """
    معالجة استيراد السجلات
    
    Args:
        records: قائمة من القواميس تمثل السجلات
        model: نموذج Django
        
    Returns:
        قاموس يحتوي على نتائج الاستيراد
    """
    total = len(records)
    success = 0
    errors = 0
    error_details = ""
    
    with transaction.atomic():
        for record in records:
            try:
                # تنظيف البيانات
                cleaned_record = clean_record(record, model)
                
                # إنشاء كائن جديد
                obj = model(**cleaned_record)
                obj.full_clean()
                obj.save()
                
                success += 1
            except Exception as e:
                errors += 1
                error_details += f"خطأ في السجل {success + errors}: {str(e)}\n"
    
    return {
        'total': total,
        'success': success,
        'errors': errors,
        'error_details': error_details
    }

def process_json_import(data, model):
    """
    معالجة استيراد ملف JSON
    
    Args:
        data: بيانات JSON
        model: نموذج Django
        
    Returns:
        قاموس يحتوي على نتائج الاستيراد
    """
    if isinstance(data, list):
        return process_records_import(data, model)
    elif isinstance(data, dict) and 'records' in data:
        return process_records_import(data['records'], model)
    else:
        raise ValueError("تنسيق ملف JSON غير صالح")

def clean_record(record, model):
    """
    تنظيف سجل قبل الاستيراد
    
    Args:
        record: قاموس يمثل السجل
        model: نموذج Django
        
    Returns:
        قاموس منظف
    """
    cleaned_record = {}
    
    # الحصول على حقول النموذج
    model_fields = {field.name: field for field in model._meta.fields}
    
    # تنظيف كل حقل
    for key, value in record.items():
        # تحويل اسم الحقل إلى snake_case إذا لزم الأمر
        field_name = key.lower().replace(' ', '_')
        
        # التحقق من وجود الحقل في النموذج
        if field_name in model_fields:
            # معالجة القيم الفارغة
            if pd.isna(value) or value == '':
                cleaned_record[field_name] = None
            else:
                cleaned_record[field_name] = value
    
    return cleaned_record

def generate_export_file(queryset, file_format='xlsx'):
    """
    إنشاء ملف تصدير
    
    Args:
        queryset: مجموعة استعلام
        file_format: تنسيق الملف (xlsx, csv, json)
        
    Returns:
        مسار الملف المؤقت
    """
    # تحويل queryset إلى قائمة من القواميس
    data = list(queryset.values())
    
    # إنشاء ملف مؤقت
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_format}') as temp_file:
        temp_path = temp_file.name
    
    # إنشاء الملف حسب التنسيق
    if file_format == 'xlsx':
        df = pd.DataFrame(data)
        df.to_excel(temp_path, index=False)
    elif file_format == 'csv':
        df = pd.DataFrame(data)
        df.to_csv(temp_path, index=False)
    elif file_format == 'json':
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        raise ValueError(f"تنسيق الملف '{file_format}' غير مدعوم")
    
    return temp_path

def generate_template(model_string):
    """
    إنشاء قالب استيراد
    
    Args:
        model_string: سلسلة نصية تمثل النموذج
        
    Returns:
        مسار الملف المؤقت
    """
    # الحصول على النموذج
    model = get_model_from_string(model_string)
    
    # الحصول على حقول النموذج
    fields = []
    for field in model._meta.fields:
        if not field.primary_key and not field.auto_created:
            fields.append(field.name)
    
    # إنشاء DataFrame فارغ
    df = pd.DataFrame(columns=fields)
    
    # إنشاء ملف مؤقت
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
        temp_path = temp_file.name
    
    # حفظ الملف
    df.to_excel(temp_path, index=False)
    
    return temp_path
