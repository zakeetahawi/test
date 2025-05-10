import React from 'react';
import { Paper, Typography, Box, BoxProps, SvgIconProps, Skeleton } from '@mui/material';
import { SvgIcon } from '@mui/material';
import { useTheme } from '@mui/material/styles';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon?: React.ComponentType<SvgIconProps>;
  trend?: {
    value: number;
    label: string;
    isPositive?: boolean;
  };
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  sx?: BoxProps['sx'];
  isLoading?: boolean;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon: Icon,
  trend,
  color = 'primary',
  sx = {},
  isLoading = false,
}) => {
  const theme = useTheme();

  const getColorByType = (type: string) => {
    switch (type) {
      case 'primary':
        return theme.palette.primary;
      case 'secondary':
        return theme.palette.secondary;
      case 'success':
        return theme.palette.success;
      case 'error':
        return theme.palette.error;
      case 'warning':
        return theme.palette.warning;
      case 'info':
        return theme.palette.info;
      default:
        return theme.palette.primary;
    }
  };

  const colorSet = getColorByType(color);

  return (
    <Paper
      sx={{
        p: 3,
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        transition: 'transform 0.2s ease-in-out',
        '&:hover': {
          transform: 'translateY(-4px)',
        },
        ...sx,
      }}
      elevation={1}
    >
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          right: 0,
          p: 2,
          opacity: 0.1,
        }}
      >
        {Icon && (
          <SvgIcon
            component={Icon}
            sx={{
              fontSize: '4rem',
              color: colorSet.main,
            }}
          />
        )}
      </Box>

      <Box sx={{ position: 'relative' }}>
        {isLoading ? (
          <Skeleton variant="text" width="60%" />
        ) : (
          <Typography
            variant="subtitle2"
            sx={{
              color: 'text.secondary',
              fontWeight: 500,
              mb: 1,
            }}
          >
            {title}
          </Typography>
        )}

        {isLoading ? (
          <Skeleton variant="rectangular" width="80%" height={40} sx={{ mb: 1 }} />
        ) : (
          <Typography
            variant="h4"
            sx={{
              color: colorSet.main,
              fontWeight: 600,
              mb: trend ? 1 : 0,
            }}
          >
            {value}
          </Typography>
        )}

        {trend && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              mt: 1,
              height: 20,
            }}
          >
            {isLoading ? (
              <Skeleton variant="text" width="100%" />
            ) : (
              <>
                <Typography
                  variant="caption"
                  sx={{
                    color: trend.isPositive ? 'success.main' : 'error.main',
                    fontWeight: 500,
                    mr: 0.5,
                  }}
                >
                  {trend.isPositive ? '+' : '-'}{trend.value}%
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: 'text.secondary',
                  }}
                >
                  {trend.label}
                </Typography>
              </>
            )}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default StatsCard;
