import React from 'react';
import { Alert, AlertTitle } from '@mui/material';
import { AxiosError } from 'axios';

interface ErrorAlertProps {
  error: unknown;
  title?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ 
  error, 
  title = 'خطأ' 
}) => {
  if (!error) return null;

  let message = 'حدث خطأ غير متوقع';
  
  if (error instanceof AxiosError) {
    message = error.response?.data?.detail || error.message;
  } else if (error instanceof Error) {
    message = error.message;
  }

  return (
    <Alert severity="error" sx={{ mb: 3 }}>
      <AlertTitle>{title}</AlertTitle>
      {message}
    </Alert>
  );
};
