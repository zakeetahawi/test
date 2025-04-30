from django import forms
from .models import GoogleSheetsConfig

class SyncIntervalForm(forms.ModelForm):
    """نموذج لتحديث فترة المزامنة"""
    
    class Meta:
        model = GoogleSheetsConfig
        fields = ['sync_interval_minutes']
        labels = {
            'sync_interval_minutes': 'فترة المزامنة (بالدقائق)'
        }
        widgets = {
            'sync_interval_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1440',  # 24 ساعة كحد أقصى
            }),
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