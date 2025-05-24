"""
نماذج إدارة قواعد البيانات على طراز أودو
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Database, Backup, BackupSchedule


class DatabaseForm(forms.ModelForm):
    """نموذج إنشاء وتعديل قاعدة البيانات"""
    
    class Meta:
        model = Database
        fields = ['name', 'db_type', 'connection_info']
        widgets = {
            'connection_info': forms.Textarea(attrs={'rows': 5, 'dir': 'ltr'}),
        }


class BackupForm(forms.ModelForm):
    """نموذج إنشاء نسخة احتياطية"""
    
    database = forms.ModelChoiceField(
        queryset=Database.objects.all(),
        label=_('قاعدة البيانات'),
        empty_label=_('-- اختر قاعدة البيانات --'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Backup
        fields = ['database', 'name', 'backup_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'backup_type': forms.Select(attrs={'class': 'form-select'}),
        }


class BackupRestoreForm(forms.Form):
    """نموذج استعادة نسخة احتياطية"""
    
    clear_data = forms.BooleanField(
        label=_('حذف البيانات الحالية قبل الاستعادة'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class BackupUploadForm(forms.Form):
    """نموذج تحميل ملف نسخة احتياطية"""
    
    database = forms.ModelChoiceField(
        queryset=Database.objects.all(),
        label=_('قاعدة البيانات'),
        empty_label=_('-- اختر قاعدة البيانات --'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    backup_file = forms.FileField(
        label=_('ملف النسخة الاحتياطية'),
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    backup_type = forms.ChoiceField(
        label=_('نوع النسخة الاحتياطية'),
        choices=Backup.BACKUP_TYPES,
        initial='full',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    clear_data = forms.BooleanField(
        label=_('حذف البيانات الحالية قبل الاستعادة'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class BackupScheduleForm(forms.ModelForm):
    """نموذج جدولة النسخ الاحتياطية"""
    
    database = forms.ModelChoiceField(
        queryset=Database.objects.all(),
        label=_('قاعدة البيانات'),
        empty_label=_('-- اختر قاعدة البيانات --'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = BackupSchedule
        fields = [
            'database', 'name', 'backup_type', 'frequency',
            'hour', 'minute', 'day_of_week', 'day_of_month',
            'max_backups', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'backup_type': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'hour': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 23}),
            'minute': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 59}),
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'max_backups': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 24}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['day_of_week'].required = False
        self.fields['day_of_month'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')
        day_of_week = cleaned_data.get('day_of_week')
        day_of_month = cleaned_data.get('day_of_month')
        
        if frequency == 'weekly' and day_of_week is None:
            self.add_error('day_of_week', _('يجب تحديد يوم الأسبوع للتكرار الأسبوعي'))
        
        if frequency == 'monthly' and day_of_month is None:
            self.add_error('day_of_month', _('يجب تحديد يوم الشهر للتكرار الشهري'))
        
        return cleaned_data
