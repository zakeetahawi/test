from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from .models import ImportExportLog, ImportTemplate

class ImportForm(forms.ModelForm):
    """
    نموذج استيراد البيانات
    """
    ALLOWED_EXTENSIONS = ['xlsx', 'csv', 'json']
    
    file = forms.FileField(
        label=_('ملف البيانات'),
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)],
        help_text=_('الملفات المدعومة: XLSX, CSV, JSON. الحد الأقصى للحجم: 50 ميجابايت'),
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    model_name = forms.ChoiceField(
        label=_('نوع البيانات'),
        choices=[
            ('multi_sheet', _('ملف متعدد الصفحات')),
            ('inventory.product', _('المنتجات')),
            ('inventory.supplier', _('الموردين')),
            ('customers.customer', _('العملاء')),
            ('orders.order', _('الطلبات')),
        ],
        help_text=_('اختر نوع البيانات التي تريد استيرادها'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_multi_sheet = forms.BooleanField(
        label=_('ملف متعدد الصفحات'),
        required=False,
        initial=False,
        help_text=_('حدد هذا الخيار إذا كان الملف يحتوي على عدة صفحات لأنواع مختلفة من البيانات'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    new_only = forms.BooleanField(
        label=_('استيراد السجلات الجديدة فقط'),
        required=False,
        initial=False,
        help_text=_('حدد هذا الخيار إذا كنت تريد استيراد السجلات الجديدة فقط دون تحديث السجلات الموجودة'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    template = forms.ModelChoiceField(
        label=_('قالب الاستيراد'),
        queryset=ImportTemplate.objects.filter(is_active=True),
        required=False,
        help_text=_('اختر قالب الاستيراد المناسب (اختياري)'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ImportExportLog
        fields = ['file', 'model_name']

    def clean_file(self):
        file = self.cleaned_data['file']
        
        # التحقق من حجم الملف (50 ميجابايت كحد أقصى)
        if file.size > 50 * 1024 * 1024:
            raise forms.ValidationError(_('حجم الملف كبير جداً. الحد الأقصى المسموح به هو 50 ميجابايت.'))
        
        # التحقق من نوع الملف
        ext = file.name.split('.')[-1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError(_('نوع الملف غير مدعوم. الأنواع المدعومة هي: XLSX, CSV, JSON'))
        
        return file

    def clean(self):
        cleaned_data = super().clean()
        
        # التحقق من توافق نوع الملف مع خيار الصفحات المتعددة
        if cleaned_data.get('is_multi_sheet'):
            ext = cleaned_data.get('file').name.split('.')[-1].lower()
            if ext != 'xlsx':
                raise forms.ValidationError(_('خيار الصفحات المتعددة متاح فقط لملفات Excel (XLSX)'))
        
        return cleaned_data

class ExportForm(forms.Form):
    """
    نموذج تصدير البيانات
    """
    model_name = forms.ChoiceField(
        label=_('نوع البيانات'),
        choices=[
            ('multi_sheet', _('ملف متعدد الصفحات')),
            ('inventory.product', _('المنتجات')),
            ('inventory.supplier', _('الموردين')),
            ('customers.customer', _('العملاء')),
            ('orders.order', _('الطلبات')),
        ],
        help_text=_('اختر نوع البيانات التي تريد تصديرها'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    export_format = forms.ChoiceField(
        label=_('صيغة الملف'),
        choices=[
            ('xlsx', 'Excel (XLSX)'),
            ('csv', 'CSV'),
            ('json', 'JSON'),
        ],
        initial='xlsx',
        help_text=_('اختر صيغة ملف التصدير'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    multi_sheet = forms.BooleanField(
        label=_('تصدير البيانات المرتبطة'),
        required=False,
        initial=True,
        help_text=_('تصدير البيانات المرتبطة في صفحات منفصلة (متاح فقط لصيغة Excel)'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'checked': 'checked'})
    )
    
    date_range = forms.ChoiceField(
        label=_('نطاق التاريخ'),
        choices=[
            ('all', _('كل البيانات')),
            ('today', _('اليوم')),
            ('week', _('الأسبوع الحالي')),
            ('month', _('الشهر الحالي')),
            ('year', _('السنة الحالية')),
        ],
        initial='all',
        required=False,
        help_text=_('اختر نطاق تاريخ البيانات المراد تصديرها'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned_data = super().clean()
        
        # التحقق من توافق خيار الصفحات المتعددة مع صيغة الملف
        if cleaned_data.get('multi_sheet') and cleaned_data.get('export_format') != 'xlsx':
            raise forms.ValidationError(_('خيار البيانات المرتبطة متاح فقط لصيغة Excel (XLSX)'))
        
        return cleaned_data

class ImportTemplateForm(forms.ModelForm):
    """
    نموذج إدارة قوالب الاستيراد
    """
    class Meta:
        model = ImportTemplate
        fields = ['name', 'description', 'model_name', 'file', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'model_name': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_file(self):
        file = self.cleaned_data['file']
        
        # التحقق من حجم الملف (5 ميجابايت كحد أقصى للقوالب)
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError(_('حجم الملف كبير جداً. الحد الأقصى المسموح به للقوالب هو 5 ميجابايت.'))
        
        # التحقق من نوع الملف (فقط Excel للقوالب)
        ext = file.name.split('.')[-1].lower()
        if ext != 'xlsx':
            raise forms.ValidationError(_('يجب أن يكون القالب بصيغة Excel (XLSX)'))
        
        return file
