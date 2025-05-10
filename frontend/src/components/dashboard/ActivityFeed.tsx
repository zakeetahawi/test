import React from 'react';
import { Paper, Typography, List, ListItem, ListItemText, ListItemIcon, Chip, Divider, Box, Skeleton } from '@mui/material';
import {
  AddCircle as AddIcon,
  Edit as EditIcon,
  Check as CheckIcon,
  Schedule as ScheduleIcon,
  Assignment as AssignmentIcon,
  NotificationsOff as NotificationsOffIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { arEG } from 'date-fns/locale';
import { EmptyState } from '../core';

interface Activity {
  id: number;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  user: string;
}

interface ActivityFeedProps {
  activities: Activity[];
  isLoading?: boolean;
}

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'create':
      return <AddIcon color="success" />;
    case 'update':
      return <EditIcon color="info" />;
    case 'complete':
      return <CheckIcon color="success" />;
    case 'schedule':
      return <ScheduleIcon color="warning" />;
    default:
      return <AssignmentIcon color="primary" />;
  }
};

const getActivityColor = (type: string) => {
  switch (type) {
    case 'create':
      return 'success';
    case 'update':
      return 'info';
    case 'complete':
      return 'success';
    case 'schedule':
      return 'warning';
    default:
      return 'primary';
  }
};

const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities, isLoading }) => {
  const skeletonCount = 5;

  if (!isLoading && activities.length === 0) {
    return (
      <EmptyState
        icon={NotificationsOffIcon}
        title="لا توجد نشاطات حديثة"
        description="لم يتم تسجيل أي نشاطات حتى الآن"
      />
    );
  }

  return (
    <Paper sx={{ height: '100%', p: 2 }}>
      <Typography variant="h6" gutterBottom>
        النشاط الأخير
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <List sx={{ width: '100%' }}>
        {isLoading ? (
          // Skeleton loading state
          Array.from(new Array(skeletonCount)).map((_, index) => (
            <React.Fragment key={index}>
              <ListItem
                sx={{
                  px: 2,
                  py: 1.5,
                }}
              >
                <ListItemIcon sx={{ mt: 1 }}>
                  <Skeleton variant="circular" width={24} height={24} />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Skeleton variant="text" width={120} />
                      <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 1 }} />
                    </Box>
                  }
                  secondary={
                    <>
                      <Skeleton variant="text" width="80%" sx={{ mb: 0.5 }} />
                      <Skeleton variant="text" width={100} />
                    </>
                  }
                />
              </ListItem>
              {index < skeletonCount - 1 && <Divider component="li" sx={{ my: 1 }} />}
            </React.Fragment>
          ))
        ) : (
          activities.map((activity, index) => (
            <React.Fragment key={activity.id}>
              <ListItem
                alignItems="flex-start"
                sx={{
                  px: 2,
                  py: 1.5,
                  '&:hover': {
                    bgcolor: 'action.hover',
                    borderRadius: 1,
                  },
                }}
              >
                <ListItemIcon sx={{ mt: 1 }}>
                  {getActivityIcon(activity.type)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="subtitle2" component="span">
                        {activity.title}
                      </Typography>
                      <Chip
                        label={activity.user}
                        size="small"
                        color={getActivityColor(activity.type) as any}
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.primary"
                        sx={{ display: 'block' }}
                      >
                        {activity.description}
                      </Typography>
                      <Typography
                        component="span"
                        variant="caption"
                        color="text.secondary"
                      >
                        {format(new Date(activity.timestamp), 'PP p', { locale: arEG })}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
              {index < activities.length - 1 && (
                <Divider component="li" sx={{ my: 1 }} />
              )}
            </React.Fragment>
          ))
        )}
      </List>
    </Paper>
  );
};

export default ActivityFeed;
