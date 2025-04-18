from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class User(AbstractUser):
    """Custom User model for the application."""
    image = models.ImageField(upload_to='users/', verbose_name=_('صورة المستخدم'), blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name=_('رقم الهاتف'), blank=True)
    branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='users', verbose_name=_('الفرع'))
    departments = models.ManyToManyField('Department', blank=True, related_name='users', verbose_name=_('الأقسام'))
    
    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمين')
    
    def __str__(self):
        return self.username

class Branch(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_main_branch = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'فرع'
        verbose_name_plural = 'الفروع'

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text='Font Awesome icon name')
    url_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'قسم'
        verbose_name_plural = 'الأقسام'

class Notification(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='read_notifications')
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    target_users = models.ManyToManyField(User, blank=True, related_name='received_notifications')
    target_department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    target_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    sender_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    
    def mark_as_read(self, user):
        """
        Mark notification as read by a specific user
        """
        from django.utils import timezone
        
        self.is_read = True
        self.read_at = timezone.now()
        self.read_by = user
        self.save()
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-created_at']

class CompanyInfo(models.Model):
    version = models.CharField(max_length=50, blank=True, default='', verbose_name='إصدار النظام')
    release_date = models.CharField(max_length=50, blank=True, default='', verbose_name='تاريخ الإطلاق')
    developer = models.CharField(max_length=100, blank=True, default='', verbose_name='المطور')
    working_hours = models.CharField(max_length=100, blank=True, default='', verbose_name='ساعات العمل')
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    commercial_register = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    social_links = models.JSONField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    vision = models.TextField(blank=True, null=True)
    mission = models.TextField(blank=True, null=True)
    primary_color = models.CharField(max_length=20, blank=True, null=True)
    secondary_color = models.CharField(max_length=20, blank=True, null=True)
    accent_color = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'معلومات الشركة'
        verbose_name_plural = 'معلومات الشركة'


class FormField(models.Model):
    FORM_TYPE_CHOICES = [
        ('customer', 'نموذج العميل'),
        ('order', 'نموذج الطلب'),
        ('inspection', 'نموذج المعاينة'),
        ('installation', 'نموذج التركيب'),
        ('product', 'نموذج المنتج'),
    ]
    
    FIELD_TYPE_CHOICES = [
        ('text', 'نص'),
        ('number', 'رقم'),
        ('email', 'بريد إلكتروني'),
        ('phone', 'هاتف'),
        ('date', 'تاريخ'),
        ('select', 'قائمة اختيار'),
        ('checkbox', 'مربع اختيار'),
        ('radio', 'زر اختيار'),
        ('textarea', 'منطقة نص'),
        ('file', 'ملف'),
    ]
    
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES)
    field_name = models.CharField(max_length=100)
    field_label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    required = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    choices = models.TextField(blank=True, null=True, help_text='قائمة الخيارات مفصولة بفواصل (للحقول من نوع select, radio, checkbox)')
    default_value = models.CharField(max_length=255, blank=True, null=True)
    help_text = models.CharField(max_length=255, blank=True, null=True)
    min_length = models.PositiveIntegerField(null=True, blank=True)
    max_length = models.PositiveIntegerField(null=True, blank=True)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f'{self.get_form_type_display()}: {self.field_label}'
    
    class Meta:
        verbose_name = 'حقل نموذج'
        verbose_name_plural = 'حقول النماذج'
        unique_together = ('form_type', 'field_name')
