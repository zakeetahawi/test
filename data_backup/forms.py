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