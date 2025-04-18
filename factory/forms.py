from django import forms
from .models import ProductionLine, ProductionOrder, ProductionStage, ProductionIssue

class ProductionLineForm(forms.ModelForm):
    """
    Form for creating and updating production lines
    """
    class Meta:
        model = ProductionLine
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم خط الإنتاج'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'وصف خط الإنتاج', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'اسم خط الإنتاج',
            'description': 'الوصف',
            'is_active': 'نشط',
        }

class ProductionOrderForm(forms.ModelForm):
    """
    Form for creating and updating production orders
    """
    class Meta:
        model = ProductionOrder
        fields = ['order', 'production_line', 'status', 'estimated_completion', 'notes']
        widgets = {
            'order': forms.Select(attrs={'class': 'form-select'}),
            'production_line': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'estimated_completion': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'ملاحظات إضافية', 'rows': 3}),
        }
        labels = {
            'order': 'الطلب',
            'production_line': 'خط الإنتاج',
            'status': 'الحالة',
            'estimated_completion': 'التاريخ المتوقع للانتهاء',
            'notes': 'ملاحظات',
        }

class ProductionStageForm(forms.ModelForm):
    """
    Form for creating and updating production stages
    """
    class Meta:
        model = ProductionStage
        fields = ['production_order', 'name', 'description', 'start_date', 'end_date', 'completed', 'notes', 'assigned_to']
        widgets = {
            'production_order': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المرحلة'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'وصف المرحلة', 'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'ملاحظات إضافية', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'production_order': 'أمر الإنتاج',
            'name': 'اسم المرحلة',
            'description': 'الوصف',
            'start_date': 'تاريخ البدء',
            'end_date': 'تاريخ الانتهاء',
            'completed': 'مكتملة',
            'notes': 'ملاحظات',
            'assigned_to': 'تم التعيين إلى',
        }

class ProductionIssueForm(forms.ModelForm):
    """
    Form for creating and updating production issues
    """
    class Meta:
        model = ProductionIssue
        fields = ['production_order', 'title', 'description', 'severity', 'resolved', 'resolution_notes']
        widgets = {
            'production_order': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان المشكلة'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'وصف المشكلة', 'rows': 3}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'ملاحظات الحل', 'rows': 3}),
        }
        labels = {
            'production_order': 'أمر الإنتاج',
            'title': 'عنوان المشكلة',
            'description': 'وصف المشكلة',
            'severity': 'خطورة المشكلة',
            'resolved': 'تم الحل',
            'resolution_notes': 'ملاحظات الحل',
        }
