"""
نماذج وحدة إدارة قواعد البيانات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
import datetime

from .models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken

class DatabaseConfigForm(forms.ModelForm):
    """نموذج إعدادات قاعدة البيانات"""

    class Meta:
        model = DatabaseConfig
        fields = [
            'name', 'db_type', 'host', 'port', 'username',
            'password', 'database_name', 'is_active', 'is_default'
        ]
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        # التحقق من وجود البيانات المطلوبة حسب نوع قاعدة البيانات
        db_type = cleaned_data.get('db_type')

        if db_type == 'postgresql' or db_type == 'mysql':
            required_fields = ['host', 'username', 'database_name']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('هذا الحقل مطلوب لنوع قاعدة البيانات المحدد.'))

        return cleaned_data


class DatabaseBackupForm(forms.ModelForm):
    """نموذج النسخ الاحتياطي لقاعدة البيانات"""

    backup_type = forms.ChoiceField(
        choices=DatabaseBackup.BACKUP_TYPES,
        initial='full',
        widget=forms.RadioSelect(),
        label=_('نوع النسخة الاحتياطية')
    )

    class Meta:
        model = DatabaseBackup
        fields = ['name', 'description', 'backup_type', 'database_config']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class DatabaseImportForm(forms.ModelForm):
    """نموذج استيراد قاعدة البيانات"""

    # خيارات استيراد البيانات
    IMPORT_MODES = [
        ('full', _('استيراد كامل (حذف البيانات القديمة)')),
        ('merge', _('دمج البيانات (الاحتفاظ بالبيانات القديمة)')),
        ('update', _('تحديث البيانات الموجودة فقط')),
        ('selective', _('استيراد انتقائي للبيانات')),
    ]

    import_mode = forms.ChoiceField(
        choices=IMPORT_MODES,
        initial='merge',
        widget=forms.RadioSelect(),
        label=_('وضع الاستيراد'),
        help_text=_('اختر طريقة استيراد البيانات.')
    )

    clear_data = forms.BooleanField(
        required=False,
        initial=False,
        label=_('حذف البيانات القديمة'),
        help_text=_('تحذير: سيؤدي هذا إلى حذف جميع البيانات الموجودة في قاعدة البيانات قبل الاستيراد.')
    )

    # خيارات استيراد انتقائية (غير مرتبطة بالنموذج)
    import_settings = forms.BooleanField(
        required=False,
        initial=True,
        label=_('استيراد الإعدادات'),
        help_text=_('استيراد إعدادات النظام.')
    )

    import_users = forms.BooleanField(
        required=False,
        initial=False,
        label=_('استيراد المستخدمين'),
        help_text=_('استيراد بيانات المستخدمين وصلاحياتهم.')
    )

    import_customers = forms.BooleanField(
        required=False,
        initial=True,
        label=_('استيراد العملاء'),
        help_text=_('استيراد بيانات العملاء.')
    )

    import_products = forms.BooleanField(
        required=False,
        initial=True,
        label=_('استيراد المنتجات'),
        help_text=_('استيراد بيانات المنتجات والمخزون.')
    )

    import_orders = forms.BooleanField(
        required=False,
        initial=True,
        label=_('استيراد الطلبات'),
        help_text=_('استيراد بيانات الطلبات.')
    )

    import_inspections = forms.BooleanField(
        required=False,
        initial=True,
        label=_('استيراد الفحوصات'),
        help_text=_('استيراد بيانات الفحوصات.')
    )

    conflict_resolution = forms.ChoiceField(
        choices=[
            ('skip', _('تخطي السجلات المتكررة')),
            ('overwrite', _('استبدال السجلات المتكررة')),
            ('keep_both', _('الاحتفاظ بالسجلات المتكررة')),
        ],
        initial='skip',
        label=_('معالجة التضارب'),
        help_text=_('كيفية التعامل مع السجلات المتكررة.')
    )

    class Meta:
        model = DatabaseImport
        fields = [
            'file', 'database_config', 'clear_data',
        ]


class SetupTokenForm(forms.ModelForm):
    """نموذج رمز الإعداد"""

    expires_in_hours = forms.IntegerField(
        initial=24,
        min_value=1,
        max_value=168,  # أسبوع
        label=_('صلاحية الرمز (بالساعات)'),
        help_text=_('عدد ساعات صلاحية الرمز.')
    )

    class Meta:
        model = SetupToken
        fields = []

    def save(self, commit=True):
        """حفظ النموذج"""
        instance = super().save(commit=False)

        # حساب وقت انتهاء الصلاحية
        expires_in_hours = self.cleaned_data.get('expires_in_hours', 24)
        instance.expires_at = timezone.now() + datetime.timedelta(hours=expires_in_hours)

        if commit:
            instance.save()

        return instance


class DatabaseSetupForm(forms.Form):
    """نموذج إعداد قاعدة البيانات"""

    db_type = forms.ChoiceField(
        choices=DatabaseConfig.DB_TYPES,
        initial='postgresql',
        label=_('نوع قاعدة البيانات')
    )

    name = forms.CharField(
        max_length=100,
        label=_('اسم قاعدة البيانات'),
        help_text=_('اسم وصفي لقاعدة البيانات.')
    )

    host = forms.CharField(
        max_length=255,
        required=False,
        label=_('المضيف'),
        help_text=_('عنوان المضيف لقاعدة البيانات.')
    )

    port = forms.CharField(
        max_length=10,
        required=False,
        label=_('المنفذ'),
        help_text=_('منفذ قاعدة البيانات.')
    )

    username = forms.CharField(
        max_length=100,
        required=False,
        label=_('اسم المستخدم'),
        help_text=_('اسم المستخدم للاتصال بقاعدة البيانات.')
    )

    password = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.PasswordInput(),
        label=_('كلمة المرور'),
        help_text=_('كلمة المرور للاتصال بقاعدة البيانات.')
    )

    database_name = forms.CharField(
        max_length=100,
        required=False,
        label=_('اسم قاعدة البيانات'),
        help_text=_('اسم قاعدة البيانات في الخادم.')
    )

    admin_username = forms.CharField(
        max_length=150,
        initial='admin',
        label=_('اسم المستخدم المدير'),
        help_text=_('اسم المستخدم للحساب المدير.')
    )

    admin_password = forms.CharField(
        max_length=128,
        initial='admin',
        widget=forms.PasswordInput(),
        label=_('كلمة مرور المدير'),
        help_text=_('كلمة المرور للحساب المدير.')
    )

    admin_email = forms.EmailField(
        max_length=254,
        initial='admin@example.com',
        required=False,
        label=_('البريد الإلكتروني للمدير'),
        help_text=_('البريد الإلكتروني للحساب المدير.')
    )

    import_file = forms.FileField(
        required=False,
        label=_('ملف الاستيراد'),
        help_text=_('ملف لاستيراد البيانات (اختياري).')
    )

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        # التحقق من وجود البيانات المطلوبة حسب نوع قاعدة البيانات
        db_type = cleaned_data.get('db_type')

        if db_type == 'postgresql' or db_type == 'mysql':
            required_fields = ['host', 'username', 'database_name']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('هذا الحقل مطلوب لنوع قاعدة البيانات المحدد.'))

        return cleaned_data
