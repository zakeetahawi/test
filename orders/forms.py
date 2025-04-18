from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem, Payment

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price', 'item_type', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
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
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    # Override order_type field to use our custom choices
    order_type = forms.ChoiceField(
        choices=ORDER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    class Meta:
        model = Order
        fields = [
            'customer', 'status', 'order_type',
            'invoice_number', 'contract_number', 'branch', 'tracking_status', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'اختر العميل'
            }),
            'tracking_status': forms.Select(attrs={'class': 'form-select'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'contract_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        for field_name in self.fields:
            self.fields[field_name].required = False
            
        # Make order_number read-only but visible
        if 'order_number' in self.fields:
            self.fields['order_number'].widget.attrs['readonly'] = True
            self.fields['order_number'].widget.attrs['class'] = 'form-control'
        else:
            # Add order_number field if it doesn't exist
            self.fields['order_number'] = forms.CharField(
                required=False,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'readonly': True,
                    'placeholder': 'سيتم إنشاؤه تلقائياً'
                }),
                label='رقم الطلب'
            )
        
        # Add service types field
        self.fields['service_types'] = forms.MultipleChoiceField(
            choices=Order.SERVICE_TYPE_CHOICES,
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            required=False,
            initial=[]
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
        order_type = cleaned_data.get('order_type')
        service_types_hidden = self.data.get('service_types_hidden', '')

        if order_type == 'service':
            # Get service types from hidden input
            service_types = [st.strip() for st in service_types_hidden.split(',') if st.strip()]
            
            # Save to cleaned_data
            cleaned_data['service_types'] = service_types
        
        # For product orders, any validation will be handled in the view
        elif order_type == 'product':
            # Clear service types for product orders
            cleaned_data['service_types'] = []

        return cleaned_data
