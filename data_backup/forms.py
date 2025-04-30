from django import forms
from .models import GoogleSheetsConfig

class SyncIntervalForm(forms.ModelForm):
    """نموذج لتحديث فترة المزامنة وخيارات المزامنة"""
    
    class Meta:
        model = GoogleSheetsConfig
        fields = [
            'sync_interval_minutes',
            'sync_customers',
            'sync_orders',
            'sync_products',
            'sync_inspections',
            'sync_installations',
            'sync_company_info',  # حقل جديد للمزامنة
            'sync_contact_details',  # حقل جديد للمزامنة
            'sync_system_settings',  # حقل جديد للمزامنة
        ]
        labels = {
            'sync_interval_minutes': 'فترة المزامنة (بالدقائق)',
            'sync_customers': 'مزامنة العملاء',
            'sync_orders': 'مزامنة الطلبات',
            'sync_products': 'مزامنة المنتجات',
            'sync_inspections': 'مزامنة المعاينات',
            'sync_installations': 'مزامنة التركيبات',
            'sync_company_info': 'مزامنة معلومات الشركة',
            'sync_contact_details': 'مزامنة بيانات التواصل',
            'sync_system_settings': 'مزامنة إعدادات النظام',
        }
        widgets = {
            'sync_interval_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1440',  # 24 ساعة كحد أقصى
            }),
            'sync_customers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_orders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_products': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_inspections': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_installations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_company_info': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_contact_details': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_system_settings': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class GoogleSheetsImportForm(forms.Form):
    """نموذج استيراد البيانات من Google Sheets"""
    model_choice = forms.ChoiceField(
        label='اختر النموذج', 
        choices=[], 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sheet_name = forms.CharField(
        label='اسم ورقة Google Sheets', 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    replace_all = forms.BooleanField(
        label='حذف البيانات الحالية واستبدالها بالبيانات المستوردة', 
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        model_choices = kwargs.pop('model_choices', [])
        super().__init__(*args, **kwargs)
        # تحويل خيارات النماذج إلى تنسيق مناسب للقائمة المنسدلة (قيمة، عرض)
        self.fields['model_choice'].choices = [(model, display_name) for model, display_name in model_choices]
        
        # إذا كانت هناك خيارات، تعيين القيمة الافتراضية للاسم الورقة نفس اسم النموذج الأول
        if model_choices:
            self.initial['sheet_name'] = model_choices[0][1]