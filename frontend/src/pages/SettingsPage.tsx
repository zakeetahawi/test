import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const SettingsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        الإعدادات
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>محتوى صفحة الإعدادات</Typography>
      </Paper>
    </Box>
  );
};

export default SettingsPage;
