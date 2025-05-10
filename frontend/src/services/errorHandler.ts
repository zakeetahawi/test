import { AxiosError } from 'axios';
import { authService } from './authService';

interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

export const handleApiError = (error: AxiosError): ApiError => {
  if (error.response) {
    // خطأ من الخادم مع رد
    const status = error.response.status;
    const data = error.response.data as any;

    switch (status) {
      case 401:
        // خطأ المصادقة
        authService.logout();
        return {
          message: 'انتهت جلسة العمل. الرجاء تسجيل الدخول مرة أخرى.',
          code: 'AUTH_ERROR',
        };
      
      case 403:
        // خطأ الصلاحيات
        return {
          message: 'ليس لديك صلاحية للقيام بهذا الإجراء.',
          code: 'PERMISSION_ERROR',
        };
      
      case 404:
        // العنصر غير موجود
        return {
          message: 'العنصر المطلوب غير موجود.',
          code: 'NOT_FOUND',
        };
      
      case 422:
        // خطأ في البيانات المدخلة
        return {
          message: 'البيانات المدخلة غير صحيحة.',
          code: 'VALIDATION_ERROR',
          details: data.errors,
        };
      
      case 429:
        // تجاوز حد الطلبات
        return {
          message: 'تم تجاوز الحد الأقصى للطلبات. الرجاء المحاولة لاحقاً.',
          code: 'RATE_LIMIT',
        };
      
      default:
        // أخطاء أخرى من الخادم
        return {
          message: data.message || 'حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى.',
          code: 'SERVER_ERROR',
          details: data,
        };
    }
  } else if (error.request) {
    // لم يتم استلام رد من الخادم
    return {
      message: 'لا يمكن الاتصال بالخادم. الرجاء التحقق من اتصال الإنترنت.',
      code: 'NETWORK_ERROR',
    };
  }

  // خطأ في إعداد الطلب
  return {
    message: 'حدث خطأ في الطلب. الرجاء المحاولة مرة أخرى.',
    code: 'REQUEST_ERROR',
  };
};