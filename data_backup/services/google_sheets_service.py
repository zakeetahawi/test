import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
from django.utils import timezone
from django.db import transaction, models
from django.db.models import ProtectedError
from django.apps import apps
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
        sheet_id = None
        
        for sheet in sheets_list:
            if sheet['properties']['title'] == sheet_name:
                sheet_exists = True
                sheet_id = sheet['properties']['sheetId']
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
        else:
            # إذا كانت الورقة موجودة، قم بمسح محتواها أولاً
            clear_request = sheets.values().clear(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1:ZZ"
            )
            clear_request.execute()
        
        # تحديث البيانات في الورقة
        range_name = f'{sheet_name}!A1'
        sheets.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body={'values': data}
        ).execute()
    
    def sync_model_data(self, spreadsheet_id, model_class, sheet_name=None):
        """مزامنة بيانات نموذج محدد مع جدول البيانات - بحيث تكون البيانات متطابقة بين النظام والجدول"""
        if sheet_name is None:
            sheet_name = model_class.__name__
            
        try:
            # الحصول على جميع السجلات والحقول من النموذج - استخدام order_by للتأكد من أن العناصر الجديدة مدرجة
            objects = model_class.objects.all().order_by('-id')
            
            # إذا لم تكن هناك سجلات، قم بمسح الجدول
            if not objects:
                # قم بإنشاء جدول فارغ مع الأعمدة فقط
                fields = [field.name for field in model_class._meta.fields]
                data = [fields]  # الصف الأول هو العناوين
                self.create_or_update_sheet(spreadsheet_id, sheet_name, data)
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
            
            # تحديث الجدول بالبيانات الجديدة فقط - سيتم مسح الجدول القديم تماماً في دالة create_or_update_sheet
            self.create_or_update_sheet(spreadsheet_id, sheet_name, data)
            
            return len(objects)
        except Exception as e:
            logger.error(f"خطأ في مزامنة نموذج {model_class.__name__}: {str(e)}")
            raise e
    
    def _prepare_field_value(self, model_class, field_name, value):
        """
        معالجة قيمة الحقل للاستيراد بناءً على نوع الحقل
        """
        # إذا كانت القيمة فارغة
        if value is None or value == '' or value == 'None':
            try:
                field = model_class._meta.get_field(field_name)
                
                # الحقول التي تقبل blank=True ولكن لا تقبل null=True تحتاج إلى قيمة فارغة بدلاً من None
                if getattr(field, 'blank', False) and not getattr(field, 'null', False):
                    if isinstance(field, models.EmailField):
                        return ''  # إرجاع سلسلة فارغة لحقل البريد الإلكتروني
                    elif isinstance(field, models.CharField):
                        return ''  # إرجاع سلسلة فارغة لحقول النصوص
                    elif isinstance(field, models.TextField):
                        return ''  # إرجاع سلسلة فارغة لحقول النص الطويل
                
                # للحقول الأخرى، نعيد None
                return None
            except:
                return None
            
        try:
            field = model_class._meta.get_field(field_name)
            
            # معالجة حقول العلاقات (ForeignKey, ManyToMany, OneToOne)
            if isinstance(field, models.ForeignKey) or isinstance(field, models.OneToOneField):
                # الحصول على الموديل المرتبط
                related_model = field.remote_field.model
                
                # محاولة البحث عن الكائن المرتبط
                if value and value != '':
                    # محاولة العثور على الكائن بواسطة المعرف أولاً
                    try:
                        if value.isdigit():
                            return related_model.objects.get(pk=value)
                    except (related_model.DoesNotExist, ValueError):
                        pass
                        
                    # محاولة العثور على الكائن بواسطة الاسم
                    try:
                        if hasattr(related_model, 'name'):
                            return related_model.objects.filter(name=value).first()
                        # إذا فشل ذلك، استخدم __str__ للبحث
                        else:
                            for obj in related_model.objects.all():
                                if str(obj) == value:
                                    return obj
                    except Exception as e:
                        logger.warning(f"فشل البحث عن الكائن المرتبط {related_model.__name__} بالقيمة {value}: {e}")
                        
                return None
            
            # معالجة حقول التاريخ والوقت
            elif isinstance(field, models.DateTimeField) or isinstance(field, models.DateField):
                if value:
                    try:
                        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            return datetime.strptime(value, '%Y-%m-%d')
                        except ValueError:
                            logger.warning(f"تنسيق تاريخ غير صالح: {value}")
                            return None
            
            # معالجة الحقول المنطقية
            elif isinstance(field, models.BooleanField):
                if value.lower() in ['true', '1', 'yes', 'نعم']:
                    return True
                elif value.lower() in ['false', '0', 'no', 'لا']:
                    return False
                return None
                
            # معالجة الحقول العددية
            elif isinstance(field, models.IntegerField) or isinstance(field, models.PositiveIntegerField):
                try:
                    return int(value) if value else None
                except (ValueError, TypeError):
                    return None
            
            elif isinstance(field, models.FloatField) or isinstance(field, models.DecimalField):
                try:
                    return float(value) if value else None
                except (ValueError, TypeError):
                    return None
            
            # معالجة حقول البريد الإلكتروني
            elif isinstance(field, models.EmailField):
                return value if value and value != 'None' else ''
            
            # إذا كان الحقل من نوع آخر، إرجاع القيمة كما هي
            return value
            
        except Exception as e:
            logger.error(f"خطأ في معالجة قيمة الحقل {field_name}: {e}")
            return value
    
    def import_data_from_sheet(self, spreadsheet_id, sheet_name, model_class, replace_all=False):
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
        
        # قراءة جميع البيانات من الجدول
        imported_data = []
        for i, row in enumerate(values[1:], start=2):  # نبدأ من 2 لأن الصف الأول للعناوين
            if not row:  # تخطي الصفوف الفارغة
                continue
                
            # توسيع الصف بالقيم الفارغة إذا كان أقصر من الصف العنواني
            row = row + [''] * (len(headers) - len(row))
            
            # بناء قاموس من الحقول والقيم
            data = {}
            for j, header in enumerate(headers):
                if j < len(row) and header:  # تأكد من وجود اسم الحقل
                    data[header] = row[j]
            
            imported_data.append(data)
        
        # استخدام المعاملة لضمان تنفيذ جميع العمليات بنجاح أو التراجع عن جميع التغييرات
        with transaction.atomic():
            try:
                # إذا تم طلب استبدال البيانات، حاول حذف البيانات الموجودة بطريقة آمنة
                if replace_all:
                    try:
                        logger.info(f"محاولة حذف جميع البيانات الموجودة في نموذج {model_class.__name__} قبل الاستيراد")
                        model_class.objects.all().delete()
                        logger.info(f"تم حذف جميع البيانات الموجودة في نموذج {model_class.__name__} بنجاح")
                    except ProtectedError as e:
                        # في حالة وجود علاقات محمية، نقوم بتحديث السجلات بدلاً من حذفها
                        protected_objects = e.protected_objects
                        logger.warning(f"تعذر حذف بعض السجلات بسبب وجود علاقات محمية: {e}")
                        logger.warning(f"سيتم تحديث السجلات الموجودة بدلاً من حذفها")
                        
                        # تخزين المعرفات الموجودة لاستخدامها لاحقًا
                        pk_field = model_class._meta.pk.name
                        existing_ids = set(model_class.objects.values_list(pk_field, flat=True))
                        
                        # إنشاء واستيراد البيانات
                        for data in imported_data:
                            if pk_field in data and data[pk_field] and data[pk_field] != 'None':
                                pk_value = data[pk_field]
                                try:
                                    # تحديث السجل الموجود
                                    instance = model_class.objects.filter(**{pk_field: pk_value}).first()
                                    if instance:
                                        for field, value in data.items():
                                            if hasattr(instance, field):
                                                processed_value = self._prepare_field_value(model_class, field, value)
                                                if processed_value is not None or field in ['notes', 'address', 'email']:  # السماح بالقيم الفارغة لبعض الحقول
                                                    setattr(instance, field, processed_value)
                                        instance.save()
                                        existing_ids.discard(pk_value)  # إزالة من القائمة لتجنب الحذف لاحقًا
                                    else:
                                        # إنشاء سجل جديد
                                        processed_data = {
                                            field: self._prepare_field_value(model_class, field, value) 
                                            for field, value in data.items()
                                        }
                                        # إزالة القيم الفارغة التي ستسبب أخطاء
                                        processed_data = {k: v for k, v in processed_data.items() if v is not None or k in ['notes', 'address', 'email']}
                                        instance = model_class(**processed_data)
                                        instance.save()
                                except Exception as e:
                                    logger.error(f"خطأ في تحديث السجل {pk_value}: {str(e)}")
                                    raise e
                            else:
                                # إنشاء سجل جديد بدون معرف محدد
                                try:
                                    processed_data = {
                                        field: self._prepare_field_value(model_class, field, value) 
                                        for field, value in data.items() if field != pk_field or not value
                                    }
                                    # إزالة القيم الفارغة التي ستسبب أخطاء
                                    processed_data = {k: v for k, v in processed_data.items() if v is not None or k in ['notes', 'address', 'email']}
                                    instance = model_class(**processed_data)
                                    instance.save()
                                except Exception as e:
                                    logger.error(f"خطأ في إنشاء سجل جديد: {str(e)}")
                                    raise e
                        
                        # حذف السجلات التي لم تعد موجودة في البيانات المستوردة - فقط إذا كان مطلوبًا
                        for old_id in existing_ids:
                            try:
                                instance = model_class.objects.filter(**{pk_field: old_id}).first()
                                if instance:
                                    instance.delete()
                            except ProtectedError:
                                logger.warning(f"تعذر حذف السجل رقم {old_id} بسبب وجود علاقات محمية")
                            except Exception as e:
                                logger.error(f"خطأ في حذف السجل رقم {old_id}: {str(e)}")
                        
                        # نعود مبكرًا لتجنب تنفيذ الكود أدناه
                        return len(imported_data)
                
                # معالجة البيانات واحدة تلو الأخرى
                imported_count = 0
                errors = []
                
                for data in imported_data:
                    try:
                        # محاولة العثور على السجل الموجود باستخدام الحقل الأساسي
                        pk_field = model_class._meta.pk.name
                        if pk_field in data and data[pk_field] and data[pk_field] != 'None':
                            # حاول التحديث إذا لم نكن في وضع الاستبدال الكامل
                            if not replace_all:
                                instance = model_class.objects.filter(**{pk_field: data[pk_field]}).first()
                                if instance:
                                    for field, value in data.items():
                                        if hasattr(instance, field) and field != pk_field:
                                            processed_value = self._prepare_field_value(model_class, field, value)
                                            if processed_value is not None or field in ['notes', 'address', 'email']:
                                                setattr(instance, field, processed_value)
                                    instance.save()
                                    imported_count += 1
                                    continue
                            
                            # إنشاء كائن جديد بالمعرف المحدد
                            processed_data = {
                                field: self._prepare_field_value(model_class, field, value) 
                                for field, value in data.items()
                            }
                            # إزالة القيم الفارغة التي ستسبب أخطاء
                            processed_data = {k: v for k, v in processed_data.items() if v is not None or k in ['notes', 'address', 'email']}
                            instance = model_class(**processed_data)
                            instance.save()
                        else:
                            # إنشاء سجل جديد بدون مفتاح أساسي محدد مسبقًا
                            processed_data = {
                                field: self._prepare_field_value(model_class, field, value) 
                                for field, value in data.items() if field != pk_field or not value
                            }
                            # إزالة القيم الفارغة التي ستسبب أخطاء
                            processed_data = {k: v for k, v in processed_data.items() if v is not None or k in ['notes', 'address', 'email']}
                            instance = model_class(**processed_data)
                            instance.save()
                            
                        imported_count += 1
                    except Exception as e:
                        detailed_error = f'خطأ في الصف {imported_count + 2}: {str(e)}'
                        logger.error(detailed_error)
                        errors.append(detailed_error)
                
                if errors:
                    raise Exception('\n'.join(errors))
                    
                return imported_count
            except Exception as e:
                # إذا حدث أي خطأ، يتم التراجع عن جميع التغييرات بسبب transaction.atomic
                logger.error(f"حدث خطأ أثناء استيراد البيانات: {str(e)}")
                raise e