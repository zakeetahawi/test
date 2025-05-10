import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const InstallationsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        التركيبات
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>محتوى صفحة التركيبات</Typography>
      </Paper>
    </Box>
  );
};

export default InstallationsPage;
