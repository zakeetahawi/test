import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

interface ErrorMessageProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message = 'حدث خطأ غير متوقع',
  onRetry
}) => {
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
        {message}
      </Typography>
      {onRetry && (
        <Button 
          variant="contained" 
          onClick={onRetry}
          sx={{ mt: 2 }}
        >
          إعادة المحاولة
        </Button>
      )}
    </Box>
  );
};