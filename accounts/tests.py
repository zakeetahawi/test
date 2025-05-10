from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import Role, UserRole

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser')

    def test_user_phone_field(self):
        self.user.phone = '0123456789'
        self.user.save()
        self.assertEqual(self.user.phone, '0123456789')

class LoginLogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
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

class RoleTests(TestCase):
    def setUp(self):
        # إنشاء مستخدم للاختبار
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # إنشاء صلاحية للاختبار
        content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
            codename='test_permission',
            name='Test Permission',
            content_type=content_type,
        )
        
    def test_role_creation(self):
        """اختبار إنشاء دور جديد"""
        role = Role.objects.create(
            name='Test Role',
            description='Test Role Description'
        )
        role.permissions.add(self.permission)
        
        self.assertEqual(role.name, 'Test Role')
        self.assertEqual(role.description, 'Test Role Description')
        self.assertEqual(role.permissions.count(), 1)
        
    def test_assign_role_to_user(self):
        """اختبار إسناد دور لمستخدم"""
        role = Role.objects.create(name='Test Role')
        role.permissions.add(self.permission)
        
        # إسناد الدور للمستخدم
        role.assign_to_user(self.user)
        
        # التحقق من إسناد الدور
        self.assertTrue(UserRole.objects.filter(user=self.user, role=role).exists())
        # التحقق من إضافة الصلاحيات
        self.assertTrue(self.user.has_perm(f"{self.permission.content_type.app_label}.{self.permission.codename}"))
        
    def test_remove_role_from_user(self):
        """اختبار إزالة دور من مستخدم"""
        role = Role.objects.create(name='Test Role')
        role.permissions.add(self.permission)
        
        # إسناد ثم إزالة الدور
        role.assign_to_user(self.user)
        role.remove_from_user(self.user)
        
        # التحقق من إزالة الدور
        self.assertFalse(UserRole.objects.filter(user=self.user, role=role).exists())
        # التحقق من إزالة الصلاحيات
        self.assertFalse(self.user.has_perm(f"{self.permission.content_type.app_label}.{self.permission.codename}"))
        
    def test_system_role_protection(self):
        """اختبار حماية أدوار النظام"""
        system_role = Role.objects.create(
            name='System Role',
            is_system_role=True
        )
        
        # التحقق من أن الدور محدد كدور نظام
        self.assertTrue(system_role.is_system_role)
