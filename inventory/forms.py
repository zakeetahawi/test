from django import forms
from .models import CustomerOrder, CustomerOrderItem

class CustomerOrderForm(forms.ModelForm):
    class Meta:
        model = CustomerOrder
        fields = ['order_number', 'customer', 'status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class CustomerOrderItemForm(forms.ModelForm):
    class Meta:
        model = CustomerOrderItem
        fields = ['product', 'quantity', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 1}),
        }

CustomerOrderItemFormSet = forms.inlineformset_factory(
    CustomerOrder, CustomerOrderItem,
    form=CustomerOrderItemForm,
    extra=1,
    can_delete=True
)
