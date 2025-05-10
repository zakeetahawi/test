import axios from 'axios';
import { store } from '../store';
import { showNotification } from '../store/slices/uiSlice';
import { AuthService } from './auth.service';

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// إضافة التوكن لكل الطلبات
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// معالجة الاستجابات والأخطاء
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // محاولة تجديد التوكن عند انتهاء صلاحيته
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const newToken = await AuthService.refreshToken();
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return axiosInstance(originalRequest);
        }
      } catch (refreshError) {
        // تسجيل الخروج إذا فشل تجديد التوكن
        AuthService.logout();
        window.location.href = '/login';
      }
    }

    // عرض رسالة خطأ للمستخدم
    const errorMessage = error.response?.data?.message || 'حدث خطأ أثناء الاتصال بالخادم';
    store.dispatch(showNotification({
      message: errorMessage,
      type: 'error'
    }));

    return Promise.reject(error);
  }
);

export default axiosInstance;