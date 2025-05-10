import React from 'react';
import { Box, Typography } from '@mui/material';

const InventoryPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        المخزون
      </Typography>
      <Typography>
        قريباً...
      </Typography>
    </Box>
  );
};

export default InventoryPage;
