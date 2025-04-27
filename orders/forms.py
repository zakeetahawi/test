from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem, Payment

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price', 'item_type', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'item_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'payment_method': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
        }

# Formset for managing multiple order items
OrderItemFormSet = forms.inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
)

class OrderForm(forms.ModelForm):
    # Override status choices to match requirements
    STATUS_CHOICES = [
        ('normal', 'عادي'),
        ('vip', 'VIP'),
    ]
    
    # Override order type choices to match requirements
    ORDER_TYPE_CHOICES = [
        ('product', 'منتج'),
        ('service', 'خدمة'),
    ]
    
    # Override status field to use our custom choices
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=False
    )

    # New field for order types
    selected_types = forms.MultipleChoiceField(
        choices=Order.ORDER_TYPES,
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Order
        fields = [
            'customer', 'status', 'invoice_number', 
            'contract_number', 'branch', 'tracking_status', 
            'notes', 'selected_types', 'delivery_type', 'delivery_address'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'data-placeholder': 'اختر العميل'
            }),
            'tracking_status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'branch': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'contract_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'notes': forms.Textarea(attrs={'class': 'form-control notes-field', 'rows': 6}),
            'delivery_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        for field_name in self.fields:
            self.fields[field_name].required = False
            
        # Make order_number read-only but visible
        if 'order_number' in self.fields:
            self.fields['order_number'].widget.attrs['readonly'] = True
            self.fields['order_number'].widget.attrs['class'] = 'form-control form-control-sm'
        else:
            # Add order_number field if it doesn't exist
            self.fields['order_number'] = forms.CharField(
                required=False,
                widget=forms.TextInput(attrs={
                    'class': 'form-control form-control-sm',
                    'readonly': True,
                    'placeholder': 'سيتم إنشاؤه تلقائياً'
                }),
                label='رقم الطلب'
            )
        
        
        # Make invoice_number and contract_number not required initially
        self.fields['invoice_number'].required = False
        self.fields['contract_number'].required = False
        
        # Set branch to user's branch if available
        if 'initial' in kwargs and 'user' in kwargs['initial']:
            user = kwargs['initial']['user']
            if hasattr(user, 'branch') and user.branch:
                self.fields['branch'].initial = user.branch
                # If not superuser, limit branch choices to user's branch
                if not user.is_superuser:
                    self.fields['branch'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        selected_types = self.data.getlist('selected_types')
        print("[DEBUG] Selected Types:", selected_types)
        print("[DEBUG] Form Data:", dict(self.data))

        # Required fields validation
        required_fields = ['customer']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'هذا الحقل مطلوب')

        if not selected_types:
            print("[DEBUG] No order types selected")
            raise forms.ValidationError({
                'selected_types': 'يجب اختيار نوع طلب واحد على الأقل'
            })

        # Contract number validation
        if 'tailoring' in selected_types and not cleaned_data.get('contract_number', '').strip():
            print("[DEBUG] Missing contract number for tailoring")
            raise forms.ValidationError({
                'contract_number': 'رقم العقد مطلوب لخدمة التفصيل'
            })

        # Invoice number validation - required for all types
        if not cleaned_data.get('invoice_number', '').strip():
            print("[DEBUG] Missing invoice number")
            raise forms.ValidationError({
                'invoice_number': 'رقم الفاتورة مطلوب'
            })

        # Delivery validation
        delivery_type = cleaned_data.get('delivery_type')
        if delivery_type == 'home' and not cleaned_data.get('delivery_address', '').strip():
            raise forms.ValidationError({
                'delivery_address': 'عنوان التوصيل مطلوب عند اختيار التوصيل للمنزل'
            })
        elif delivery_type == 'branch' and not cleaned_data.get('branch'):
            raise forms.ValidationError({
                'branch': 'يجب اختيار الفرع عند اختيار الاستلام من الفرع'
            })

        # Backward compatibility
        has_products = any(t in ['fabric', 'accessory'] for t in selected_types)
        has_services = any(t in ['installation', 'inspection', 'transport', 'tailoring'] for t in selected_types)
        
        cleaned_data['order_type'] = 'product' if has_products else 'service'
        if has_services:
            cleaned_data['service_types'] = [t for t in selected_types if t in ['installation', 'inspection', 'transport', 'tailoring']]
        
        print("[DEBUG] Final cleaned data:", cleaned_data)
        return cleaned_data
