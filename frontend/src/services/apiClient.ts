import axios from 'axios';

// إنشاء نسخة من Axios مع الإعدادات الأساسية
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// إضافة معترض للطلبات لإضافة token المصادقة
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// إضافة معترض للاستجابات للتعامل مع الأخطاء
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // محاولة تجديد التوكن
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post('/api/token/refresh/', {
            refresh: refreshToken,
          });
          
          localStorage.setItem('auth_token', response.data.access);
          
          // إعادة المحاولة بالتوكن الجديد
          error.config.headers.Authorization = `Bearer ${response.data.access}`;
          return apiClient(error.config);
        } catch {
          // فشل تجديد التوكن، تسجيل الخروج
          localStorage.removeItem('auth_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;