from django import forms
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from .models import ImportExportLog, ImportTemplate

class ImportForm(forms.ModelForm):
    """
    Form for importing data
    """
    model_name = forms.ChoiceField(
        label=_('نموذج البيانات'),
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_('اختر نوع البيانات التي تريد استيرادها. إذا كنت تستخدم ملف متعدد الصفحات، سيتم تجاهل هذا الخيار وسيتم تحديد النوع تلقائياً من اسم الصفحة.')
    )
    
    file = forms.FileField(
        label=_('ملف البيانات'),
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    is_multi_sheet = forms.BooleanField(
        label=_('ملف متعدد الصفحات'),
        required=False,
        initial=True,
        help_text=_('حدد هذا الخيار إذا كان الملف يحتوي على صفحات متعددة لأنواع مختلفة من البيانات. سيتم تحديد نوع البيانات تلقائياً من اسم الصفحة.'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = ImportExportLog
        fields = ['model_name', 'file', 'is_multi_sheet']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all models that can be imported
        importable_models = [
            ('multi_sheet', _('ملف متعدد الصفحات (تحديد تلقائي)')),
            ('inventory.product', _('المنتجات')),
            ('inventory.supplier', _('الموردين')),
            ('customers.customer', _('العملاء')),
            ('orders.order', _('الطلبات')),
        ]
        
        self.fields['model_name'].choices = importable_models

class ExportForm(forms.ModelForm):
    """
    Form for exporting data
    """
    model_name = forms.ChoiceField(
        label=_('نموذج البيانات'),
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    export_format = forms.ChoiceField(
        label=_('صيغة التصدير'),
        choices=[
            ('xlsx', _('Excel (.xlsx)')),
            ('csv', _('CSV (.csv)')),
            ('json', _('JSON (.json)')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    multi_sheet = forms.BooleanField(
        label=_('تصدير متعدد الصفحات'),
        required=False,
        initial=True,
        help_text=_('تصدير البيانات في ملف Excel متعدد الصفحات (يعمل فقط مع صيغة Excel)'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'checked': 'checked'})
    )
    
    class Meta:
        model = ImportExportLog
        fields = ['model_name']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all models that can be exported
        exportable_models = [
            ('inventory.product', _('المنتجات')),
            ('inventory.supplier', _('الموردين')),
            ('customers.customer', _('العملاء')),
            ('orders.order', _('الطلبات')),
            ('inventory.stocktransaction', _('حركات المخزون')),
            ('inventory.purchaseorder', _('طلبات الشراء')),
        ]
        
        self.fields['model_name'].choices = exportable_models

class ImportTemplateForm(forms.ModelForm):
    """
    Form for import templates
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all models that can be imported
        importable_models = [
            ('inventory.product', _('المنتجات')),
            ('inventory.supplier', _('الموردين')),
            ('customers.customer', _('العملاء')),
            ('orders.order', _('الطلبات')),
        ]
        
        self.fields['model_name'].choices = importable_models
