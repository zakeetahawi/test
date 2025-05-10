import React from 'react';
import { Card, CardContent, Typography, Box, Icon } from '@mui/material';
import { styled } from '@mui/material/styles';

interface StatsCardProps {
  title: string;
  value: string;
  icon: string;
  trend: string;
}

const IconWrapper = styled(Box)(({ theme }) => ({
  width: 48,
  height: 48,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: theme.palette.primary.light,
  color: theme.palette.primary.main,
}));

const TrendIndicator = styled(Typography)<{ trend: string }>(({ theme, trend }) => ({
  color: trend.startsWith('+') ? theme.palette.success.main : theme.palette.error.main,
  fontSize: '0.875rem',
  fontWeight: 500,
  display: 'flex',
  alignItems: 'center',
  '&::before': {
    content: '""',
    width: 0,
    height: 0,
    marginRight: 4,
    borderLeft: '4px solid transparent',
    borderRight: '4px solid transparent',
    borderBottom: trend.startsWith('+') 
      ? `4px solid ${theme.palette.success.main}`
      : 'none',
    borderTop: trend.startsWith('-') 
      ? `4px solid ${theme.palette.error.main}`
      : 'none',
  }
}));

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, trend }) => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" mb={2}>
          <Box>
            <Typography variant="subtitle2" color="textSecondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
          </Box>
          <IconWrapper>
            <Icon>{icon}</Icon>
          </IconWrapper>
        </Box>
        <TrendIndicator trend={trend}>
          {trend}
        </TrendIndicator>
      </CardContent>
    </Card>
  );
};

export default StatsCard;