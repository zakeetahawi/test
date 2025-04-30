import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """خدمة التعامل مع Google Sheets API"""
    
    def __init__(self, credentials_file):
        """تهيئة الخدمة مع ملف بيانات الاعتماد"""
        credentials_path = os.path.join(settings.MEDIA_ROOT, credentials_file.name)
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        
    def create_or_update_sheet(self, spreadsheet_id, sheet_name, data):
        """إنشاء أو تحديث ورقة في جدول البيانات"""
        sheets = self.service.spreadsheets()
        
        # التحقق مما إذا كانت الورقة موجودة
        sheet_metadata = sheets.get(spreadsheetId=spreadsheet_id).execute()
        sheets_list = sheet_metadata.get('sheets', '')
        sheet_exists = False
        
        for sheet in sheets_list:
            if sheet['properties']['title'] == sheet_name:
                sheet_exists = True
                break
                
        # إنشاء ورقة جديدة إذا لم تكن موجودة
        if not sheet_exists:
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }
            sheets.batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request]}
            ).execute()
        
        # تحديث البيانات في الورقة
        range_name = f'{sheet_name}!A1'
        sheets.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body={'values': data}
        ).execute()
        
    def sync_model_data(self, spreadsheet_id, model_class, sheet_name=None):
        """مزامنة بيانات نموذج محدد مع جدول البيانات"""
        if sheet_name is None:
            sheet_name = model_class.__name__
            
        try:
            # الحصول على جميع السجلات والحقول من النموذج - استخدام order_by للتأكد من أن العناصر الجديدة مدرجة
            objects = model_class.objects.all().order_by('-id')
            
            # إذا لم تكن هناك سجلات، لا داعي للمتابعة
            if not objects:
                logger.warning(f"لا توجد سجلات للمزامنة في نموذج {model_class.__name__}")
                return 0
                
            # استخراج أسماء الحقول
            fields = [field.name for field in model_class._meta.fields]
            
            # تحضير البيانات للتصدير
            data = [fields]  # الصف الأول هو العناوين
            
            for obj in objects:
                row = []
                for field in fields:
                    try:
                        value = getattr(obj, field)
                        # معالجة القيم الخاصة مثل التواريخ والعلاقات
                        if hasattr(value, 'pk'):
                            # إذا كان الحقل علاقة، حاول الحصول على اسم الكائن المرتبط
                            if hasattr(value, 'get_full_name') and callable(value.get_full_name):
                                value = value.get_full_name()
                            elif hasattr(value, 'name'):
                                value = value.name
                            elif hasattr(value, '__str__'):
                                value = str(value)
                            else:
                                value = f"{value.pk}"
                        elif isinstance(value, datetime):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                            
                        row.append(str(value) if value is not None else '')
                    except Exception as e:
                        logger.error(f"خطأ في معالجة الحقل {field} للكائن {obj.pk}: {str(e)}")
                        row.append('')
                        
                data.append(row)
            
            # تحديث الجدول
            self.create_or_update_sheet(spreadsheet_id, sheet_name, data)
            
            return len(objects)
        except Exception as e:
            logger.error(f"خطأ في مزامنة نموذج {model_class.__name__}: {str(e)}")
            raise e

    def import_data_from_sheet(self, spreadsheet_id, sheet_name, model_class):
        """استيراد البيانات من ورقة جوجل إلى قاعدة البيانات"""
        sheets = self.service.spreadsheets()
        
        # الحصول على بيانات الورقة
        result = sheets.values().get(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A:ZZ'
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) <= 1:
            return 0  # لا توجد بيانات أو فقط الصف العنواني
        
        # الصف الأول يحتوي على أسماء الحقول
        headers = values[0]
        
        # معالجة الصفوف المتبقية
        imported_count = 0
        errors = []
        
        for i, row in enumerate(values[1:], start=2):  # نبدأ من 2 لأن الصف الأول للعناوين
            # تأكد من أن الصف يحتوي على بيانات
            if not row:
                continue
                
            # توسيع الصف بالقيم الفارغة إذا كان أقصر من الصف العنواني
            row = row + [''] * (len(headers) - len(row))
            
            # بناء قاموس من الحقول والقيم
            data = {}
            for j, header in enumerate(headers):
                if j < len(row):
                    data[header] = row[j]
            
            try:
                # محاولة العثور على السجل الموجود باستخدام الحقل الأساسي
                pk_field = model_class._meta.pk.name
                if pk_field in data and data[pk_field] and data[pk_field] != 'None':
                    # حاول التحديث
                    instance = model_class.objects.filter(**{pk_field: data[pk_field]}).first()
                    if instance:
                        for field, value in data.items():
                            if hasattr(instance, field) and field != pk_field:
                                setattr(instance, field, value if value else None)
                        instance.save()
                    else:
                        # في حال عدم وجود السجل، قم بإنشائه
                        instance = model_class(**data)
                        instance.save()
                else:
                    # إنشاء سجل جديد بدون مفتاح أساسي
                    new_data = {k: v for k, v in data.items() if k != pk_field}
                    instance = model_class(**new_data)
                    instance.save()
                    
                imported_count += 1
            except Exception as e:
                errors.append(f'خطأ في الصف {i}: {str(e)}')
        
        if errors:
            raise Exception('\n'.join(errors))
            
        return imported_count