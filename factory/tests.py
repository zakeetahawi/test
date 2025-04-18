from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from orders.models import Order
from .models import ProductionLine, ProductionOrder

class ProductionLineModelTest(TestCase):
    def setUp(self):
        self.line = ProductionLine.objects.create(name='خط 1')

    def test_production_line_str(self):
        self.assertEqual(str(self.line), 'خط 1')

    def test_production_line_unique_name(self):
        with self.assertRaises(Exception):
            ProductionLine.objects.create(name='خط 1')

class ProductionOrderModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='produser', password='testpass123')
        self.line = ProductionLine.objects.create(name='خط 2')
        from customers.models import Customer, CustomerCategory
        self.category = CustomerCategory.objects.create(name='VIP')
        self.customer = Customer.objects.create(
            name='عميل إنتاج',
            code='CUST500',
            phone='01000009999',
            email='prod@example.com',
            customer_type='retail',
            status='active',
            category=self.category
        )
        self.order = Order.objects.create(
            customer=self.customer,
            delivery_type='branch',
            order_number='ORDP001',
            status='normal',
            order_type='product',
            tracking_status='pending',
            service_types=[]
        )
        self.prod_order = ProductionOrder.objects.create(
            order=self.order,
            production_line=self.line,
            status='pending',
            created_by=self.user
        )

    def test_production_order_str(self):
        self.assertIn('ORDP001', str(self.prod_order))

class ProductionLineViewsTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='produser', password='testpass123')
        self.client = Client()
        self.line = ProductionLine.objects.create(name='خط 3')
        self.client.login(username='produser', password='testpass123')

    def test_production_line_list_view(self):
        response = self.client.get(reverse('factory:production_line_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'خط 3')

    def test_production_line_create_view(self):
        response = self.client.post(reverse('factory:production_line_create'), {
            'name': 'خط جديد'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProductionLine.objects.filter(name='خط جديد').exists())

    def test_production_line_delete_view(self):
        response = self.client.post(reverse('factory:production_line_delete', args=[self.line.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ProductionLine.objects.filter(id=self.line.id).exists())
