import React from 'react';
import { Box, Typography, Button, Paper, SxProps } from '@mui/material';
import { Error as ErrorIcon } from '@mui/icons-material';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  sx?: SxProps;
}

const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'حدث خطأ',
  message = 'عذراً، حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.',
  onRetry,
  sx = {},
}) => {
  return (
    <Paper
      sx={{
        p: 4,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        ...sx,
      }}
    >
      <ErrorIcon
        sx={{
          fontSize: 64,
          color: 'error.main',
          mb: 2,
        }}
      />
      <Typography variant="h6" gutterBottom color="error">
        {title}
      </Typography>
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ mb: onRetry ? 3 : 0 }}
      >
        {message}
      </Typography>
      {onRetry && (
        <Button
          variant="contained"
          color="primary"
          onClick={onRetry}
          sx={{ mt: 2 }}
        >
          إعادة المحاولة
        </Button>
      )}
    </Paper>
  );
};

export default ErrorState;
