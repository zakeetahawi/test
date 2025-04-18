from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from orders.models import Order
from accounts.models import Branch
from customers.models import Customer
from .models import Installation

class InstallationModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='instuser', password='testpass123')
        self.branch = Branch.objects.create(name='فرع تركيبات')
        self.customer = Customer.objects.create(
            name='عميل تركيبات',
            code='CUST300',
            phone='01000005555',
            email='inst@example.com',
            customer_type='retail',
            status='active'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            delivery_type='branch',
            order_number='ORDINST1',
            status='normal',
            order_type='product',
            tracking_status='pending',
            service_types=[]
        )
        self.installation = Installation.objects.create(
            order=self.order,
            customer=self.customer,
            branch=self.branch,
            invoice_number='INV001',
            status='pending'
        )

    def test_installation_str(self):
        self.assertIn('تركيب', str(self.installation))  # تحقق عام من وجود كلمة تركيب

class InstallationViewsTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='instuser', password='testpass123')
        self.client = Client()
        self.branch = Branch.objects.create(name='فرع تركيبات')
        self.customer = Customer.objects.create(
            name='عميل تركيبات',
            code='CUST301',
            phone='01000006666',
            email='inst2@example.com',
            customer_type='retail',
            status='active'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            delivery_type='branch',
            order_number='ORDINST2',
            status='normal',
            order_type='product',
            tracking_status='pending',
            service_types=[]
        )
        self.installation = Installation.objects.create(
            order=self.order,
            customer=self.customer,
            branch=self.branch,
            invoice_number='INV002',
            status='pending',
            team_leader=self.user
        )
        self.client.login(username='instuser', password='testpass123')

    def test_installation_list_view(self):
        response = self.client.get(reverse('installations:installation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'INV002')

    def test_installation_create_view(self):
        response = self.client.post(reverse('installations:installation_create'), {
            'order': self.order.id,
            'customer': self.customer.id,
            'branch': self.branch.id,
            'invoice_number': 'INV003',
            'status': 'pending',
            'team_leader': self.user.id,
            'scheduled_date': '2025-04-18',
            'notes': 'Test installation'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Installation.objects.filter(invoice_number='INV003').exists())

    def test_installation_delete_view(self):
        response = self.client.post(reverse('installations:installation_delete', args=[self.installation.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Installation.objects.filter(id=self.installation.id).exists())
