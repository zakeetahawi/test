"""
Create a test order with shipping details to demonstrate the shipping integration
"""
import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from customers.models import Customer
from accounts.models import Branch
from orders.models import Order, OrderItem, Product
from orders.services.shipping_service import ShippingService

def create_test_order():
    # Use the admin user
    User = get_user_model()
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        raise Exception("Admin user not found. Please ensure the admin user exists in the system.")

    # Get first available branch
    branch = Branch.objects.first()
    if not branch:
        raise Exception("No branch found in the system. Please ensure at least one branch exists.")

    # Get or create test customer
    customer, _ = Customer.objects.get_or_create(
        name='عميل تجريبي',
        defaults={
            'phone': '0500000000',
            'address': 'الرياض - حي النخيل',
            'email': 'test.customer@example.com'
        }
    )

    # Get or create test product
    product, _ = Product.objects.get_or_create(
        name='قماش تجريبي',
        defaults={
            'description': 'قماش تجريبي للاختبار',
            'price': 100,
            'stock': 50
        }
    )

    # Create order
    order = Order.objects.create(
        customer=customer,
        delivery_type='home',
        delivery_address='الرياض - حي النخيل - شارع الأمير محمد بن سلمان',
        created_by=user,
        branch=branch,
        total_amount=1000,
        selected_types=['fabric'],
        tracking_status='pending'
    )

    # Create order item
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        unit_price=product.price,
        item_type='fabric'
    )

    # Create shipping details using the shipping service
    shipping = ShippingService.create_shipping_details(
        order=order,
        shipping_provider='aramex',
        tracking_number='TEST123456',
        estimated_delivery_date=timezone.now() + datetime.timedelta(days=3),
        shipping_cost=50,
        recipient_name=customer.name,
        recipient_phone=customer.phone,
        shipping_notes='طلب تجريبي لاختبار نظام الشحن'
    )

    # Update shipping status to demonstrate status changes
    ShippingService.update_shipping_status(
        order=order,
        new_status='scheduled',
        notes='تم جدولة الشحنة للتسليم'
    )

    print(f"""
تم إنشاء طلب تجريبي بنجاح:
- رقم الطلب: {order.order_number}
- العميل: {order.customer.name}
- عنوان التسليم: {order.delivery_address}
- حالة الشحن: {shipping.get_shipping_status_display()}
- شركة الشحن: {shipping.get_shipping_provider_display()}
- رقم التتبع: {shipping.tracking_number}
- تاريخ التسليم المتوقع: {shipping.estimated_delivery_date}
""")

    return order

if __name__ == '__main__':
    create_test_order()
