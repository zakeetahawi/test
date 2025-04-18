from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from customers.models import Customer
from accounts.models import Branch
from .models import Inspection

class InspectionModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='inspuser', password='testpass123')
        self.branch = Branch.objects.create(name='فرع المعاينة')
        self.customer = Customer.objects.create(
            name='عميل المعاينة',
            code='CUST200',
            phone='01000003333',
            email='insp@example.com',
            customer_type='retail',
            status='active'
        )
        self.inspection = Inspection.objects.create(
            contract_number='CNTR001',
            customer=self.customer,
            branch=self.branch,
            request_date='2025-04-01',
            scheduled_date='2025-04-10',
            status='pending',
            created_by=self.user
        )

    def test_inspection_str(self):
        self.assertIn('CNTR001', str(self.inspection))

    def test_contract_number_unique(self):
        with self.assertRaises(Exception):
            Inspection.objects.create(
                contract_number='CNTR001',
                customer=self.customer,
                branch=self.branch,
                request_date='2025-04-02',
                scheduled_date='2025-04-11',
                status='pending',
                created_by=self.user
            )

class InspectionViewsTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='inspuser', password='testpass123')
        self.client = Client()
        self.branch = Branch.objects.create(name='فرع المعاينة')
        self.customer = Customer.objects.create(
            name='عميل المعاينة',
            code='CUST201',
            phone='01000004444',
            email='insp2@example.com',
            customer_type='retail',
            status='active'
        )
        self.inspection = Inspection.objects.create(
            contract_number='CNTR002',
            customer=self.customer,
            branch=self.branch,
            request_date='2025-04-05',
            scheduled_date='2025-04-15',
            status='pending',
            created_by=self.user
        )
        self.client.login(username='inspuser', password='testpass123')

    def test_inspection_list_view(self):
        response = self.client.get(reverse('inspections:inspection_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CNTR002')

    def test_inspection_create_view(self):
        response = self.client.post(reverse('inspections:inspection_create'), {
            'contract_number': 'CNTR003',
            'customer': self.customer.id,
            'branch': self.branch.id,
            'request_date': '2025-04-10',
            'scheduled_date': '2025-04-20',
            'status': 'pending',
            'created_by': self.user.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Inspection.objects.filter(contract_number='CNTR003').exists())

    def test_inspection_delete_view(self):
        response = self.client.post(reverse('inspections:inspection_delete', args=[self.inspection.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Inspection.objects.filter(id=self.inspection.id).exists())
