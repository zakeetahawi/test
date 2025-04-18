from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import User, Branch, Department, CompanyInfo, FormField

class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form with Bootstrap styling
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم المستخدم')}),
        label=_('اسم المستخدم')
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('كلمة المرور')}),
        label=_('كلمة المرور')
    )

class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration
    """
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'branch', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم المستخدم')}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الاسم الأول')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الاسم الأخير')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('البريد الإلكتروني')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('رقم الهاتف')}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': _('كلمة المرور')})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': _('تأكيد كلمة المرور')})

class UserUpdateForm(forms.ModelForm):
    """
    Form for updating user information
    """
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'branch')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم المستخدم')}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الاسم الأول')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الاسم الأخير')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('البريد الإلكتروني')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('رقم الهاتف')}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Custom password change form with Bootstrap styling
    """
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('كلمة المرور الحالية')}),
        label=_('كلمة المرور الحالية')
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('كلمة المرور الجديدة')}),
        label=_('كلمة المرور الجديدة')
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('تأكيد كلمة المرور الجديدة')}),
        label=_('تأكيد كلمة المرور الجديدة')
    )

class BranchForm(forms.ModelForm):
    """
    Form for creating and updating branches
    """
    class Meta:
        model = Branch
        fields = ('code', 'name', 'address', 'phone', 'email', 'is_active', 'is_main_branch')
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('كود الفرع')}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم الفرع')}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('العنوان'), 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('رقم الهاتف')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('البريد الإلكتروني')}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_main_branch': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DepartmentForm(forms.ModelForm):
    """
    Form for creating and updating departments
    """
    class Meta:
        model = Department
        fields = ('name', 'code', 'description', 'icon', 'url_name', 'is_active', 'order')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم القسم')}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('كود القسم')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('الوصف'), 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('أيقونة')}),
            'url_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم URL')}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('الترتيب')}),
        }

class CompanyInfoForm(forms.ModelForm):
    """
    Form for updating company information
    """
    class Meta:
        model = CompanyInfo
        exclude = ['developer']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم الشركة')}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('وصف الشركة'), 'rows': 3}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('العنوان'), 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('رقم الهاتف')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('البريد الإلكتروني')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('الموقع الإلكتروني')}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الرقم الضريبي')}),
            'commercial_register': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('السجل التجاري')}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('فيسبوك')}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('تويتر')}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('انستغرام')}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('لينكد إن')}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('نبذة عن الشركة'), 'rows': 4}),
            'vision': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('رؤية الشركة'), 'rows': 4}),
            'mission': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('رسالة الشركة'), 'rows': 4}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }

class FormFieldForm(forms.ModelForm):
    """
    Form for creating and updating form fields
    """
    class Meta:
        model = FormField
        fields = ('form_type', 'field_name', 'field_label', 'field_type', 'required', 'enabled', 'order', 
                 'choices', 'min_length', 'max_length', 'min_value', 'max_value', 'help_text', 'default_value')
        widgets = {
            'form_type': forms.Select(attrs={'class': 'form-select'}),
            'field_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم الحقل')}),
            'field_label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('عنوان الحقل')}),
            'field_type': forms.Select(attrs={'class': 'form-select'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('الترتيب')}),
            'choices': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('الخيارات مفصولة بفاصلة'), 'rows': 3}),
            'min_length': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('الحد الأدنى للطول')}),
            'max_length': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('الحد الأقصى للطول')}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('الحد الأدنى للقيمة')}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('الحد الأقصى للقيمة')}),
            'help_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('نص المساعدة')}),
            'default_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('القيمة الافتراضية')}),
        }
