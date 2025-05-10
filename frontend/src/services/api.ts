import axios, { AxiosInstance, AxiosError } from 'axios';
import { useSnackbar } from '../components/core/Snackbar';
import type { SnackbarContextType } from '../components/core/Snackbar/types';

// Create base axios instance
const baseURL = import.meta.env.VITE_API_URL || '/api';

const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error types
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, string[]>;
}

// Error handler
const handleApiError = (error: AxiosError): ApiError => {
  if (error.response) {
    // Server responded with error
    const data = error.response.data as any;
    return {
      message: data.message || 'حدث خطأ في الخادم',
      code: data.code,
      details: data.details,
    };
  } else if (error.request) {
    // Request made but no response
    return {
      message: 'لا يمكن الوصول إلى الخادم',
      code: 'NETWORK_ERROR',
    };
  } else {
    // Error in request configuration
    return {
      message: 'حدث خطأ في الطلب',
      code: 'REQUEST_ERROR',
    };
  }
};

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(handleApiError(error))
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError = handleApiError(error);
    
    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    
    return Promise.reject(apiError);
  }
);

// API hooks and utilities
export const useApi = () => {
  // Assert type to ensure proper typing throughout the API service
  const snackbarContext = useSnackbar() as unknown as SnackbarContextType;

  const handleError = (error: ApiError) => {
    if (error.details) {
      // Show detailed validation errors
      const messages = Object.values(error.details).flat();
      messages.forEach(msg => snackbarContext.showError(msg));
    } else {
      // Show general error message
      snackbarContext.showError(error.message);
    }
    return Promise.reject(error);
  };

  const handleSuccess = (message: string) => {
    snackbarContext.showSuccess(message);
  };

  return {
    get: <T>(url: string) => 
      api.get<T>(url).catch(handleError),
    
    post: <T>(url: string, data?: any) => 
      api.post<T>(url, data).catch(handleError),
    
    put: <T>(url: string, data?: any) => 
      api.put<T>(url, data).catch(handleError),
    
    patch: <T>(url: string, data?: any) => 
      api.patch<T>(url, data).catch(handleError),
    
    delete: <T>(url: string) => 
      api.delete<T>(url).catch(handleError),
    
    // Helper method for file uploads
    upload: <T>(url: string, file: File, onProgress?: (progress: number) => void) => {
      const formData = new FormData();
      formData.append('file', file);
      
      return api.post<T>(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      }).catch(handleError);
    },

    // Re-export utility functions
    handleSuccess,
    handleError,
  };
};

export default api;
