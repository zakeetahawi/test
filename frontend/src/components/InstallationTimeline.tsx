import React from 'react';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from '@mui/lab';
import {
  Paper,
  Typography,
  Box,
  useTheme,
} from '@mui/material';
import {
  CheckCircleOutline,
  Error,
  Warning,
  Info,
  DirectionsCar,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { arEG } from 'date-fns/locale';
import { InstallationTimelineEvent } from '../types/installation';

interface Props {
  events: InstallationTimelineEvent[];
}

export const InstallationTimeline: React.FC<Props> = ({ events }) => {
  const theme = useTheme();

  const getEventIcon = (severity?: string) => {
    switch (severity) {
      case 'success':
        return <CheckCircleOutline color="success" />;
      case 'error':
        return <Error color="error" />;
      case 'warning':
        return <Warning color="warning" />;
      default:
        return <Info color="info" />;
    }
  };

  const getEventColor = (severity?: string) => {
    switch (severity) {
      case 'success':
        return theme.palette.success.main;
      case 'error':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      default:
        return theme.palette.info.main;
    }
  };

  return (
    <Timeline position="right" sx={{ direction: 'rtl' }}>
      {events.map((event) => (
        <TimelineItem key={event.id}>
          <TimelineSeparator>
            <TimelineDot sx={{ bgcolor: getEventColor(event.severity) }}>
              {getEventIcon(event.severity)}
            </TimelineDot>
            <TimelineConnector />
          </TimelineSeparator>
          <TimelineContent>
            <Paper elevation={3} sx={{ p: 2, mb: 2, borderRadius: 2 }}>
              <Typography variant="h6" component="h3" gutterBottom>
                {event.title}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {event.description}
              </Typography>
              <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                <Typography variant="caption" color="textSecondary">
                  {formatDistanceToNow(new Date(event.timestamp), {
                    addSuffix: true,
                    locale: arEG,
                  })}
                </Typography>
              </Box>
              {event.type === 'team_update' && (
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <DirectionsCar fontSize="small" />
                  <Typography variant="caption">فريق التركيب في الطريق</Typography>
                </Box>
              )}
            </Paper>
          </TimelineContent>
        </TimelineItem>
      ))}
    </Timeline>
  );
};