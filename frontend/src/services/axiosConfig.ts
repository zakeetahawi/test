import axios from 'axios';
import { store } from '../store';
import { logout } from '../store/slices/authSlice';

// إعداد الـ interceptor للتعامل مع توكن المصادقة
axios.interceptors.request.use(
  (config) => {
    const state = store.getState();
    const token = state.auth.tokens?.access;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// إعداد الـ interceptor للتعامل مع الأخطاء
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      store.dispatch(logout());
    }
    return Promise.reject(error);
  }
);