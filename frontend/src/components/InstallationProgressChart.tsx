import React from 'react';
import { Box, CircularProgress, Typography, useTheme } from '@mui/material';

interface Props {
  progress: number;
  estimatedTimeRemaining?: number;
}

export const InstallationProgressChart: React.FC<Props> = ({ progress, estimatedTimeRemaining }) => {
  const theme = useTheme();

  const formatTime = (minutes?: number) => {
    if (!minutes) return 'غير محدد';
    if (minutes < 60) return `${minutes} دقيقة`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours} ساعة ${remainingMinutes > 0 ? `و ${remainingMinutes} دقيقة` : ''}`;
  };

  return (
    <Box sx={{ position: 'relative', display: 'inline-flex', flexDirection: 'column', alignItems: 'center' }}>
      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
        <CircularProgress
          variant="determinate"
          value={100}
          size={120}
          thickness={4}
          sx={{ color: theme.palette.grey[200] }}
        />
        <CircularProgress
          variant="determinate"
          value={progress}
          size={120}
          thickness={4}
          sx={{
            color: theme.palette.primary.main,
            position: 'absolute',
            left: 0,
          }}
        />
        <Box
          sx={{
            top: 0,
            left: 0,
            bottom: 0,
            right: 0,
            position: 'absolute',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography
            variant="h4"
            component="div"
            color="text.primary"
            sx={{ fontWeight: 'bold' }}
          >
            {Math.round(progress)}%
          </Typography>
        </Box>
      </Box>
      {estimatedTimeRemaining !== undefined && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 2, textAlign: 'center' }}
        >
          الوقت المتبقي: {formatTime(estimatedTimeRemaining)}
        </Typography>
      )}
    </Box>
  );
};