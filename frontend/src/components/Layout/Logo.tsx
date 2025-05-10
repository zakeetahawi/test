import React from 'react';
import { Box, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';

interface LogoStyleProps {
  height?: number;
  textColor?: string;
}

export const Logo: React.FC<LogoStyleProps> = ({ height = 40, textColor }) => {
  const theme = useTheme();
  
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
      }}
    >
      <img
        src="/img/logo.png"
        alt="شعار النظام"
        style={{
          height: `${height}px`,
          width: 'auto',
        }}
      />
      <Typography
        variant="h6"
        component="div"
        sx={{
          color: textColor || theme.palette.primary.main,
          fontWeight: 'bold',
          fontSize: `${height * 0.5}px`,
        }}
      >
        نظام الخواجة
      </Typography>
    </Box>
  );
};
