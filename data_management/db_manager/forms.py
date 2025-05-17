from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DatabaseConfig, DatabaseBackup, DatabaseImport, SetupToken
import os
from datetime import datetime, timedelta


class DatabaseConfigForm(forms.ModelForm):
    """نموذج إدخال إعدادات قاعدة البيانات"""

    password = forms.CharField(
        label=_('كلمة المرور'),
        widget=forms.PasswordInput(),
        required=False,
        help_text=_('اترك هذا الحقل فارغًا إذا كنت لا ترغب في تغيير كلمة المرور')
    )

    class Meta:
        model = DatabaseConfig
        fields = [
            'name', 'db_type', 'host', 'port', 'username', 'password',
            'database_name', 'connection_string', 'is_active', 'is_default'
        ]
        widgets = {
            'connection_string': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية بناءً على نوع قاعدة البيانات
        self.fields['host'].required = False
        self.fields['port'].required = False
        self.fields['username'].required = False
        self.fields['database_name'].required = False
        self.fields['connection_string'].required = False

        # تعيين قاعدة البيانات كنشطة افتراضيًا
        if not self.instance.pk:  # فقط للسجلات الجديدة
            self.fields['is_active'].initial = True

            # إذا لم توجد قاعدة بيانات افتراضية، نقوم بتعيين هذه القاعدة كافتراضية
            if not DatabaseConfig.objects.filter(is_default=True).exists():
                self.fields['is_default'].initial = True

        # إضافة فئات Bootstrap
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        db_type = cleaned_data.get('db_type')

        # التحقق من الحقول المطلوبة بناءً على نوع قاعدة البيانات
        if db_type == 'postgresql' or db_type == 'mysql':
            if not cleaned_data.get('host'):
                self.add_error('host', _('هذا الحقل مطلوب لقواعد بيانات PostgreSQL و MySQL'))
            if not cleaned_data.get('database_name'):
                self.add_error('database_name', _('هذا الحقل مطلوب لقواعد بيانات PostgreSQL و MySQL'))

        # التحقق من أن هناك قاعدة بيانات افتراضية واحدة فقط
        if cleaned_data.get('is_default'):
            # سيتم التعامل مع هذا في طريقة save
            pass

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # إذا كان هذا الإعداد هو الافتراضي، قم بإلغاء تعيين الإعدادات الأخرى كافتراضية
        if instance.is_default and commit:
            DatabaseConfig.objects.exclude(pk=instance.pk).update(is_default=False)

        if commit:
            instance.save()

        return instance


class DatabaseBackupForm(forms.ModelForm):
    """نموذج إدخال النسخ الاحتياطية لقواعد البيانات"""

    class Meta:
        model = DatabaseBackup
        fields = ['name', 'description', 'backup_type', 'database_config']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تحديد قواعد البيانات النشطة فقط
        self.fields['database_config'].queryset = DatabaseConfig.objects.filter(is_active=True)

        # تحديد قاعدة البيانات الافتراضية
        default_db = DatabaseConfig.objects.filter(is_default=True).first()
        if default_db:
            self.fields['database_config'].initial = default_db.id

        # إضافة فئات Bootstrap
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user:
            instance.created_by = self.user

        if commit:
            instance.save()

        return instance


class DatabaseImportForm(forms.ModelForm):
    """نموذج استيراد قاعدة بيانات"""

    file = forms.FileField(
        label=_('ملف الاستيراد'),
        help_text=_('يجب أن يكون الملف بتنسيق JSON أو SQL أو DUMP'),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.json,.sql,.dump'})
    )

    clear_data = forms.BooleanField(
        label=_('حذف البيانات القديمة'),
        required=False,
        initial=False,
        help_text=_('حذف البيانات الموجودة في قاعدة البيانات قبل استيراد البيانات الجديدة')
    )

    class Meta:
        model = DatabaseImport
        fields = ['file', 'database_config', 'clear_data']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تحديد قواعد البيانات النشطة فقط
        self.fields['database_config'].queryset = DatabaseConfig.objects.filter(is_active=True)

        # تحديد قاعدة البيانات الافتراضية
        default_db = DatabaseConfig.objects.filter(is_default=True).first()
        if default_db:
            self.fields['database_config'].initial = default_db.id

        # إضافة فئات Bootstrap
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.json', '.sql', '.dump']:
                raise forms.ValidationError(_('يجب أن يكون الملف بتنسيق JSON أو SQL أو DUMP'))

            # التحقق من حجم الملف (الحد الأقصى 100 ميجابايت)
            if file.size > 100 * 1024 * 1024:
                raise forms.ValidationError(_('حجم الملف كبير جدًا. الحد الأقصى هو 100 ميجابايت'))

        return file

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user:
            instance.created_by = self.user

        if commit:
            instance.save()

        return instance


class SetupTokenForm(forms.ModelForm):
    """نموذج إنشاء رمز إعداد جديد"""

    expiry_hours = forms.IntegerField(
        label=_('ساعات الصلاحية'),
        initial=24,
        min_value=1,
        max_value=168,  # أسبوع
        help_text=_('عدد الساعات التي سيظل فيها الرمز صالحًا')
    )

    class Meta:
        model = SetupToken
        fields = []  # لا نحتاج إلى أي حقول من النموذج

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # إضافة فئات Bootstrap
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        instance = super().save(commit=False)

        # تعيين تاريخ انتهاء الصلاحية
        expiry_hours = self.cleaned_data.get('expiry_hours', 24)
        instance.expires_at = datetime.now() + timedelta(hours=expiry_hours)

        if commit:
            instance.save()

        return instance


class DatabaseSetupForm(forms.Form):
    """نموذج الإعداد الأولي لقاعدة البيانات"""

    db_type = forms.ChoiceField(
        label=_('نوع قاعدة البيانات'),
        choices=DatabaseConfig.DB_TYPES,
        initial='postgresql',
        widget=forms.RadioSelect(),
        help_text=_('اختر نوع قاعدة البيانات التي تريد استخدامها')
    )

    # حقول PostgreSQL و MySQL
    host = forms.CharField(
        label=_('المضيف'),
        required=False,
        help_text=_('عنوان الخادم المستضيف لقاعدة البيانات (مثال: localhost)')
    )
    port = forms.CharField(
        label=_('المنفذ'),
        required=False,
        help_text=_('منفذ الاتصال بقاعدة البيانات (مثال: 5432 لـ PostgreSQL، 3306 لـ MySQL)')
    )
    database_name = forms.CharField(
        label=_('اسم قاعدة البيانات'),
        required=False,
        help_text=_('اسم قاعدة البيانات التي تريد الاتصال بها')
    )
    username = forms.CharField(
        label=_('اسم المستخدم'),
        required=False,
        help_text=_('اسم المستخدم للاتصال بقاعدة البيانات')
    )
    password = forms.CharField(
        label=_('كلمة المرور'),
        widget=forms.PasswordInput(),
        required=False,
        help_text=_('كلمة المرور للاتصال بقاعدة البيانات')
    )

    # حقول SQLite
    sqlite_file = forms.FileField(
        label=_('ملف SQLite'),
        required=False,
        help_text=_('اختر ملف قاعدة بيانات SQLite موجود أو اترك فارغًا لإنشاء ملف جديد')
    )

    # حقول مشتركة
    create_superuser = forms.BooleanField(
        label=_('إنشاء مستخدم مسؤول'),
        initial=True,
        required=False,
        help_text=_('إنشاء مستخدم مسؤول جديد للنظام')
    )
    admin_username = forms.CharField(
        label=_('اسم المستخدم المسؤول'),
        required=False,
        help_text=_('اسم المستخدم للمسؤول الجديد')
    )
    admin_email = forms.EmailField(
        label=_('البريد الإلكتروني للمسؤول'),
        required=False,
        help_text=_('البريد الإلكتروني للمسؤول الجديد')
    )
    admin_password = forms.CharField(
        label=_('كلمة مرور المسؤول'),
        widget=forms.PasswordInput(),
        required=False,
        help_text=_('كلمة المرور للمسؤول الجديد')
    )
    admin_password_confirm = forms.CharField(
        label=_('تأكيد كلمة المرور'),
        widget=forms.PasswordInput(),
        required=False,
        help_text=_('أعد إدخال كلمة المرور للتأكيد')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # إضافة فئات Bootstrap
        for field_name, field in self.fields.items():
            if field_name != 'db_type':  # استثناء حقل نوع قاعدة البيانات لأنه يستخدم RadioSelect
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        db_type = cleaned_data.get('db_type')
        create_superuser = cleaned_data.get('create_superuser')

        # التحقق من الحقول المطلوبة بناءً على نوع قاعدة البيانات
        if db_type in ['postgresql', 'mysql']:
            for field in ['host', 'database_name', 'username']:
                if not cleaned_data.get(field):
                    self.add_error(field, _('هذا الحقل مطلوب لقواعد بيانات PostgreSQL و MySQL'))

        # التحقق من حقول المستخدم المسؤول إذا تم اختيار إنشاء مستخدم مسؤول
        if create_superuser:
            for field in ['admin_username', 'admin_email', 'admin_password', 'admin_password_confirm']:
                if not cleaned_data.get(field):
                    self.add_error(field, _('هذا الحقل مطلوب عند إنشاء مستخدم مسؤول'))

            # التحقق من تطابق كلمات المرور
            if cleaned_data.get('admin_password') != cleaned_data.get('admin_password_confirm'):
                self.add_error('admin_password_confirm', _('كلمات المرور غير متطابقة'))

        return cleaned_data
