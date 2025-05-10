import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const FactoryPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        المصنع
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>محتوى صفحة المصنع</Typography>
      </Paper>
    </Box>
  );
};

export default FactoryPage;
