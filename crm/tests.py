from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from customers.models import Customer
from orders.models import Order
from factory.models import ProductionOrder
from inventory.models import Product, Category

class HomeViewTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='dashboarduser', password='testpass123')
        self.client = Client()
        self.client.login(username='dashboarduser', password='testpass123')
        self.customer = Customer.objects.create(
            name='عميل للوحة المعلومات',
            code='CUST400',
            phone='01000007777',
            email='dashboard@example.com',
            customer_type='retail',
            status='active'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            delivery_type='branch',
            order_number='ORDDASH1',
            status='normal',
            order_type='product',
            tracking_status='pending',
            service_types=[]
        )
        self.prod_order = ProductionOrder.objects.create(
            order=self.order,
            status='pending',
            created_by=self.user
        )
        self.category = Category.objects.create(name='فئة افتراضية')
        self.product = Product.objects.create(
            name='منتج لوحة المعلومات',
            code='PRDDASH1',
            category=self.category,
            unit='piece',
            price=100
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'لوحة')

    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'عن النظام')

    def test_contact_view(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'اتصل')
