import React from 'react';
import { Paper, Typography, Button, Stack, Divider, Box, Skeleton } from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  Description as DescriptionIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface QuickActionsProps {
  isLoading?: boolean;
}

const QuickActions: React.FC<QuickActionsProps> = ({ isLoading }) => {
  const navigate = useNavigate();

  const actions = [
    {
      label: 'عميل جديد',
      description: 'إضافة عميل جديد للنظام',
      icon: <AddIcon />,
      path: '/customers/new',
      color: 'primary',
    },
    {
      label: 'معاينة جديدة',
      description: 'جدولة معاينة جديدة',
      icon: <SearchIcon />,
      path: '/inspections/new',
      color: 'warning',
    },
    {
      label: 'طلب جديد',
      description: 'تسجيل طلب جديد',
      icon: <DescriptionIcon />,
      path: '/orders/new',
      color: 'info',
    },
    {
      label: 'جدولة تركيب',
      description: 'إضافة موعد تركيب جديد',
      icon: <ScheduleIcon />,
      path: '/installations/new',
      color: 'success',
    },
  ] as const;

  return (
    <Paper sx={{ height: '100%', p: 2 }}>
      <Typography variant="h6" gutterBottom>
        إجراءات سريعة
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <Stack spacing={2}>
        {isLoading ? (
          // Skeleton loading state
          Array.from(new Array(4)).map((_, index) => (
            <Box
              key={index}
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Stack direction="row" spacing={1} alignItems="center">
                <Skeleton variant="circular" width={24} height={24} />
                <Box sx={{ flex: 1 }}>
                  <Skeleton variant="text" width="40%" />
                  <Skeleton variant="text" width="60%" />
                </Box>
              </Stack>
            </Box>
          ))
        ) : (
          actions.map((action) => (
            <Button
              key={action.label}
              variant="outlined"
              color={action.color}
              startIcon={action.icon}
              onClick={() => navigate(action.path)}
              sx={{
                justifyContent: 'flex-start',
                py: 1.5,
                px: 2,
                '&:hover': {
                  backgroundColor: `${action.color}.lighter`,
                },
              }}
            >
              <Box>
                <Typography variant="subtitle2" align="right">
                  {action.label}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  display="block"
                  align="right"
                >
                  {action.description}
                </Typography>
              </Box>
            </Button>
          ))
        )}
      </Stack>
    </Paper>
  );
};

export default QuickActions;
