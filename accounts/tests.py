from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

class UserModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='testuser', password='testpass123')

    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser')

    def test_user_phone_field(self):
        self.user.phone = '0123456789'
        self.user.save()
        self.assertEqual(self.user.phone, '0123456789')

class LoginLogoutViewTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()

    def test_login_view_success(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'testuser', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 302)  # Redirect after login

    def test_login_view_fail(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'wrong', 'password': 'wrong'})
        self.assertContains(response, 'اسم المستخدم أو كلمة المرور غير صحيحة', status_code=200)

    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
