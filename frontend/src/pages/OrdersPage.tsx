import React from 'react';
import { Box, Typography } from '@mui/material';

const OrdersPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        الطلبات
      </Typography>
      <Typography>
        قريباً...
      </Typography>
    </Box>
  );
};

export default OrdersPage;
