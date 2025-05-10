from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import json

from .models import Report, ReportSchedule

class ReportForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_types = [
            ('sales', _('تقرير المبيعات')),
            ('inspection', _('تقرير المعاينات')),
            ('production', _('تقرير الإنتاج')),
            ('inventory', _('تقرير المخزون')),
            ('financial', _('تقرير مالي')),
            ('analytics', _('تقرير تحليلي')),
        ]
        self.fields['report_type'].choices = allowed_types

    class Meta:
        model = Report
        fields = ['title', 'report_type', 'description', 'parameters']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'parameters': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_parameters(self):
        """Validate JSON parameters"""
        parameters = self.cleaned_data.get('parameters')
        if parameters:
            try:
                # Attempt to parse JSON
                json_data = json.loads(parameters)
                if not isinstance(json_data, dict):
                    raise ValidationError(_('المعلمات يجب أن تكون كائن JSON صحيح'))
                return json_data
            except json.JSONDecodeError:
                raise ValidationError(_('تنسيق JSON غير صحيح'))
        return {}

class ReportScheduleForm(forms.ModelForm):
    class Meta:
        model = ReportSchedule
        fields = ['name', 'frequency', 'parameters', 'recipients']
        widgets = {
            'parameters': forms.Textarea(attrs={'rows': 4}),
            'recipients': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

    def clean_parameters(self):
        """Validate JSON parameters"""
        parameters = self.cleaned_data.get('parameters')
        if parameters:
            try:
                # Attempt to parse JSON
                json_data = json.loads(parameters)
                if not isinstance(json_data, dict):
                    raise ValidationError(_('المعلمات يجب أن تكون كائن JSON صحيح'))
                return json_data
            except json.JSONDecodeError:
                raise ValidationError(_('تنسيق JSON غير صحيح'))
        return {}
