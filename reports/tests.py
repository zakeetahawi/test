from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Report

class ReportModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='reportuser', password='testpass123')
        self.report = Report.objects.create(
            title='تقرير مبيعات',
            report_type='sales',
            created_by=self.user
        )

    def test_report_str(self):
        self.assertEqual(str(self.report), 'تقرير مبيعات')

class ReportViewsTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='reportuser', password='testpass123')
        self.client = Client()
        self.client.login(username='reportuser', password='testpass123')
        self.report = Report.objects.create(
            title='تقرير مبيعات',
            report_type='sales',
            created_by=self.user
        )

    def test_report_list_view(self):
        response = self.client.get(reverse('reports:report_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تقرير مبيعات')

    def test_report_create_view(self):
        response = self.client.post(reverse('reports:report_create'), {
            'title': 'تقرير جديد',
            'report_type': 'inventory',
            'description': 'وصف تجريبي',
            'parameters': '{}'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Report.objects.filter(title='تقرير جديد').exists())

    def test_report_delete_view(self):
        response = self.client.post(reverse('reports:report_delete', args=[self.report.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Report.objects.filter(id=self.report.id).exists())
