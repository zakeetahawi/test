from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Installation, InstallationStep, InstallationQualityCheck


class InstallationForm(forms.ModelForm):
    """نموذج إنشاء وتعديل التركيب"""
    
    class Meta:
        model = Installation
        fields = ['order', 'inspection', 'team', 'scheduled_date', 'status', 'quality_rating', 'notes']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # تحسين حقول الاختيار
        self.fields['order'].empty_label = _("اختر الطلب")
        self.fields['inspection'].empty_label = _("اختر المعاينة (اختياري)")
        self.fields['team'].empty_label = _("اختر فريق التركيب (اختياري)")
        
        # تقييد الاختيارات حسب فرع المستخدم
        if self.user and not self.user.is_superuser and hasattr(self.user, 'branch') and self.user.branch:
            self.fields['order'].queryset = self.fields['order'].queryset.filter(branch=self.user.branch)
            self.fields['inspection'].queryset = self.fields['inspection'].queryset.filter(branch=self.user.branch)
            self.fields['team'].queryset = self.fields['team'].queryset.filter(branch=self.user.branch)
    
    def clean_scheduled_date(self):
        """التحقق من تاريخ التركيب المجدول"""
        scheduled_date = self.cleaned_data.get('scheduled_date')
        
        if scheduled_date and scheduled_date < timezone.now().date():
            raise ValidationError(_("لا يمكن جدولة التركيب في تاريخ سابق"))
            
        return scheduled_date
    
    def clean(self):
        """التحقق من البيانات المدخلة"""
        cleaned_data = super().clean()
        order = cleaned_data.get('order')
        status = cleaned_data.get('status')
        
        # التحقق من أن الطلب تم سداده
        if order and not order.payment_verified:
            self.add_error('order', _("لا يمكن إنشاء طلب تركيب لطلب لم يتم التحقق من سداده"))
        
        # التحقق من حالة التركيب
        if status == 'completed' and not self.instance.actual_start_date:
            self.add_error('status', _("لا يمكن تحديد التركيب كمكتمل قبل بدء العمل عليه"))
            
        return cleaned_data


class InstallationStepForm(forms.ModelForm):
    """نموذج إنشاء خطوة تركيب"""
    
    class Meta:
        model = InstallationStep
        fields = ['name', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def clean_order(self):
        """التحقق من ترتيب الخطوة"""
        order = self.cleaned_data.get('order')
        
        if order <= 0:
            raise ValidationError(_("يجب أن يكون الترتيب رقمًا موجبًا"))
            
        return order


class InstallationQualityCheckForm(forms.ModelForm):
    """نموذج إنشاء فحص جودة"""
    
    class Meta:
        model = InstallationQualityCheck
        fields = ['criteria', 'rating', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def clean_rating(self):
        """التحقق من التقييم"""
        rating = self.cleaned_data.get('rating')
        
        if rating < 1 or rating > 5:
            raise ValidationError(_("يجب أن يكون التقييم بين 1 و 5"))
            
        return rating
