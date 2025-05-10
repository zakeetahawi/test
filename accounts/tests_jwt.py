from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class JWTAuthenticationTests(APITestCase):
    """
    اختبارات لنظام المصادقة JWT
    """
    
    def setUp(self):
        # إنشاء مستخدم للاختبار
        self.username = "testuser"
        self.password = "testpassword123"
        self.user = User.objects.create_user(
            username=self.username, 
            password=self.password,
            email="test@example.com"
        )

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
    def test_obtain_token(self):
        """
        اختبار الحصول على رمز JWT
        """
        url = reverse('token_obtain_pair')
        data = {'username': self.username, 'password': self.password}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_refresh_token(self):
        """
        اختبار تحديث رمز JWT
        """
        tokens = self.get_tokens_for_user(self.user)
        url = reverse('token_refresh')
        data = {'refresh': tokens['refresh']}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
    def test_verify_token(self):
        """
        اختبار التحقق من رمز JWT
        """
        tokens = self.get_tokens_for_user(self.user)
        url = reverse('token_verify')
        data = {'token': tokens['access']}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_access_protected_endpoint(self):
        """
        اختبار الوصول إلى نقطة نهاية محمية باستخدام JWT
        """
        # محاولة الوصول بدون مصادقة
        url = reverse('accounts:api_current_user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # المصادقة باستخدام JWT
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        # محاولة الوصول بعد المصادقة
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.username)