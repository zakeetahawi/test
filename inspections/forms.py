from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import Branch, User
from .models import (
    Inspection,
    InspectionEvaluation,
    InspectionReport,
    InspectionNotification
)

class InspectionEvaluationForm(forms.ModelForm):
    class Meta:
        model = InspectionEvaluation
        fields = ['criteria', 'rating', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

class InspectionReportForm(forms.ModelForm):
    class Meta:
        model = InspectionReport
        fields = ['title', 'report_type', 'branch', 'date_from', 'date_to', 'notes']
        widgets = {
            'date_from': forms.DateInput(attrs={'type': 'date'}),
            'date_to': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_to < date_from:
            raise ValidationError(_('تاريخ النهاية يجب أن يكون بعد تاريخ البداية'))

        return cleaned_data

class InspectionNotificationForm(forms.ModelForm):
    class Meta:
        model = InspectionNotification
        fields = ['type', 'message', 'scheduled_for']
        widgets = {
            'scheduled_for': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'message': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean_scheduled_for(self):
        scheduled_for = self.cleaned_data.get('scheduled_for')
        if scheduled_for and scheduled_for < timezone.now():
            raise ValidationError(_('لا يمكن تحديد موعد في الماضي'))
        return scheduled_for

class InspectionFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': _('بحث...')
    }))
    status = forms.ChoiceField(
        choices=[('', _('كل الحالات'))] + Inspection.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        empty_label=_('كل الفروع'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = [
            'contract_number',
            'customer',
            'inspector',
            'branch',
            'request_date',
            'scheduled_date',
            'status',
            'result',
            'notes'
        ]
        widgets = {
            'request_date': forms.DateInput(attrs={'type': 'date'}),
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set inspector queryset to show only active users
        self.fields['inspector'].queryset = User.objects.filter(is_active=True)
        
        # Set default branch if user is not superuser
        if user and not user.is_superuser:
            self.fields['branch'].initial = user.branch
            self.fields['branch'].widget.attrs['readonly'] = True
            self.fields['branch'].disabled = True
        
        # Make fields optional as needed
        self.fields['notes'].required = False
        self.fields['result'].required = False
        self.fields['customer'].required = False
        self.fields['contract_number'].required = False
        self.fields['inspector'].required = True
        
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

        # Custom labels in Arabic
        self.fields['contract_number'].label = _('رقم العقد')
        self.fields['customer'].label = _('العميل')
        self.fields['inspector'].label = _('المعاين')
        self.fields['branch'].label = _('الفرع')
        self.fields['request_date'].label = _('تاريخ الطلب')
        self.fields['scheduled_date'].label = _('تاريخ التنفيذ')
        self.fields['status'].label = _('الحالة')
        self.fields['result'].label = _('النتيجة')
        self.fields['notes'].label = _('ملاحظات')

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        result = cleaned_data.get('result')
        scheduled_date = cleaned_data.get('scheduled_date')
        request_date = cleaned_data.get('request_date')

        # Validation: If status is completed, result is required
        if status == 'completed' and not result:
            self.add_error('result', _('يجب تحديد النتيجة عند اكتمال المعاينة'))

        # Validation: scheduled_date should be after or equal to request_date
        if request_date and scheduled_date and scheduled_date < request_date:
            self.add_error('scheduled_date', _('تاريخ التنفيذ يجب أن يكون بعد أو يساوي تاريخ الطلب'))

        # Validation: scheduled_date is required
        if not scheduled_date:
            self.add_error('scheduled_date', _('يجب تحديد تاريخ التنفيذ'))

        return cleaned_data
