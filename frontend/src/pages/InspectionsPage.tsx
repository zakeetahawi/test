import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const InspectionsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        المعاينات
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>محتوى صفحة المعاينات</Typography>
      </Paper>
    </Box>
  );
};

export default InspectionsPage;
