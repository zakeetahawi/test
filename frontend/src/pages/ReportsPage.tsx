import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const ReportsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        التقارير
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>محتوى صفحة التقارير</Typography>
      </Paper>
    </Box>
  );
};

export default ReportsPage;
