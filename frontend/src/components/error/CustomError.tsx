import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

interface CustomErrorProps {
  status?: number;
  message?: string;
}

export const CustomError: React.FC<CustomErrorProps> = ({ 
  status = 404, 
  message = 'الصفحة غير موجودة' 
}) => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '80vh',
        gap: 2
      }}
    >
      <Typography variant="h1" component="h1">
        {status}
      </Typography>
      <Typography variant="h5" component="h2">
        {message}
      </Typography>
      <Button 
        variant="contained" 
        color="primary" 
        onClick={() => navigate('/dashboard')}
      >
        العودة إلى لوحة التحكم
      </Button>
    </Box>
  );
};
