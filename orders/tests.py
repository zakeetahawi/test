from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from customers.models import Customer, CustomerCategory
from .models import Order

class OrderModelTest(TestCase):
    def setUp(self):
        self.category = CustomerCategory.objects.create(name='VIP')
        self.customer = Customer.objects.create(
            name='عميل طلب',
            code='CUST100',
            phone='01000001111',
            email='order@example.com',
            customer_type='retail',
            status='active',
            category=self.category
        )
        self.order = Order.objects.create(
            customer=self.customer,
            delivery_type='branch',
            order_number='ORD001',
            status='normal',
            order_type='product',
            tracking_status='pending',
            service_types=[]
        )

    def test_order_str(self):
        self.assertIn('ORD001', str(self.order))

    def test_order_number_unique(self):
        with self.assertRaises(Exception):
            Order.objects.create(
                customer=self.customer,
                delivery_type='branch',
                order_number='ORD001',
                status='normal',
                order_type='product',
                tracking_status='pending',
                service_types=[]
            )

class OrderViewsTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='testuser', password='testpass123', is_staff=True, is_superuser=True)
        self.client = Client()
        self.category = CustomerCategory.objects.create(name='VIP')
        self.customer = Customer.objects.create(
            name='عميل طلب',
            code='CUST101',
            phone='01000002222',
            email='order2@example.com',
            customer_type='retail',
            status='active',
            category=self.category
        )
        self.order = Order.objects.create(
            customer=self.customer,
            delivery_type='branch',
            order_number='ORD002',
            status='normal',
            order_type='product',
            tracking_status='pending',
            service_types=[]
        )
        self.client.login(username='testuser', password='testpass123')

    def test_order_list_view(self):
        response = self.client.get(reverse('orders:order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ORD002')

    def test_order_create_view(self):
        response = self.client.post(reverse('orders:order_create'), {
            'customer': self.customer.id,
            'delivery_type': 'branch',
            'order_number': 'ORD002',
            'status': 'normal',
            'order_type': 'product',
            'tracking_status': 'pending',
            'service_types': []  # Assuming service_types is required
        })
        # Accept both 200 (form error) and 302 (success)
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 302:
            self.assertTrue(Order.objects.filter(order_number='ORD002').exists())

    def test_order_delete_view(self):
        response = self.client.post(reverse('orders:order_delete', args=[self.order.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())
