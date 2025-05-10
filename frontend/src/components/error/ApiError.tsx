import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import RefreshIcon from '@mui/icons-material/Refresh';

interface ApiErrorProps {
  error: any;
  onRetry?: () => void;
}

export const ApiError: React.FC<ApiErrorProps> = ({ error, onRetry }) => {
  const getErrorMessage = (error: any): string => {
    if (typeof error === 'string') return error;
    
    if (error.response) {
      // خطأ من الخادم مع استجابة
      const { status } = error.response;
      if (status === 404) return 'لم يتم العثور على البيانات المطلوبة';
      if (status === 401) return 'غير مصرح لك بالوصول. الرجاء تسجيل الدخول مجدداً';
      if (status === 403) return 'ليس لديك صلاحية للوصول إلى هذا المورد';
      if (status === 500) return 'حدث خطأ في الخادم. الرجاء المحاولة لاحقاً';
      
      // رسالة الخطأ من الخادم إذا كانت موجودة
      return error.response.data?.message || 'حدث خطأ أثناء الاتصال بالخادم';
    }

    if (error.request) {
      // تم إرسال الطلب لكن لم يتم تلقي استجابة
      return 'لم نتمكن من الاتصال بالخادم. الرجاء التحقق من اتصالك بالإنترنت';
    }

    // خطأ في إعداد الطلب
    return error.message || 'حدث خطأ غير متوقع';
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        p: 3,
        textAlign: 'center'
      }}
    >
      <ErrorOutlineIcon color="error" sx={{ fontSize: 48, mb: 2 }} />
      <Typography variant="h6" color="error" gutterBottom>
        {getErrorMessage(error)}
      </Typography>
      {onRetry && (
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={onRetry}
          sx={{ mt: 2 }}
        >
          إعادة المحاولة
        </Button>
      )}
    </Box>
  );
};