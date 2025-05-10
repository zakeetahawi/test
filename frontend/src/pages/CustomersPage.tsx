import React from 'react';
import { Box, Typography } from '@mui/material';

const CustomersPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        العملاء
      </Typography>
      <Typography>
        قريباً...
      </Typography>
    </Box>
  );
};

export default CustomersPage;
