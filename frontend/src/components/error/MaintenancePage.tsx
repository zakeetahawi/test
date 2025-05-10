import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import BuildIcon from '@mui/icons-material/Build';
import RefreshIcon from '@mui/icons-material/Refresh';

interface MaintenancePageProps {
  onRetry?: () => void;
  message?: string;
  estimatedTime?: string;
}

export const MaintenancePage: React.FC<MaintenancePageProps> = ({
  onRetry,
  message = 'النظام قيد الصيانة حالياً',
  estimatedTime
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        textAlign: 'center',
        p: 3,
        backgroundColor: 'background.default'
      }}
    >
      <BuildIcon sx={{ fontSize: 80, color: 'warning.main', mb: 3 }} />
      <Typography variant="h4" gutterBottom>
        {message}
      </Typography>
      {estimatedTime && (
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          الوقت المتوقع لاستكمال الصيانة: {estimatedTime}
        </Typography>
      )}
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        نعتذر عن الإزعاج. نعمل على تحسين النظام لخدمتكم بشكل أفضل.
      </Typography>
      {onRetry && (
        <Button
          variant="contained"
          color="primary"
          startIcon={<RefreshIcon />}
          onClick={onRetry}
          sx={{ mt: 2 }}
        >
          تحديث الصفحة
        </Button>
      )}
    </Box>
  );
};