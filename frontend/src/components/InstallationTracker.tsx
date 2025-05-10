import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Stack,
} from '@mui/material';
import { InstallationConsumer } from './InstallationConsumer';
import { InstallationTimeline } from './InstallationTimeline';
import { InstallationProgressChart } from './InstallationProgressChart';
import { InstallationHeatmap } from './InstallationHeatmap';
import { InstallationDelayAlert } from './InstallationDelayAlert';
import { InstallationUpdate, InstallationTimelineEvent } from '../types/installation';

interface Props {
  installationId: string;
}

export const InstallationTracker: React.FC<Props> = ({ installationId }) => {
  const [currentProgress, setCurrentProgress] = React.useState(0);
  const [timeRemaining, setTimeRemaining] = React.useState<number>();
  const [timelineEvents, setTimelineEvents] = React.useState<InstallationTimelineEvent[]>([]);
  const [delays, setDelays] = React.useState<Array<{
    stepName: string;
    delayMinutes: number;
    reason?: string;
    severity: 'warning' | 'error';
  }>>([]);

  // Sample heatmap data - in production this would come from an API
  const heatmapData = React.useMemo(() => [
    {
      region: 'المنطقة الشرقية',
      hour: '09:00',
      value: 3
    },
    {
      region: 'المنطقة الغربية',
      hour: '09:00',
      value: 5
    },
    {
      region: 'المنطقة الشمالية',
      hour: '09:00',
      value: 2
    },
    {
      region: 'المنطقة الجنوبية',
      hour: '09:00',
      value: 4
    },
    // Add data for other hours
    {
      region: 'المنطقة الشرقية',
      hour: '10:00',
      value: 4
    },
    {
      region: 'المنطقة الغربية',
      hour: '10:00',
      value: 3
    },
    {
      region: 'المنطقة الشمالية',
      hour: '10:00',
      value: 5
    },
    {
      region: 'المنطقة الجنوبية',
      hour: '10:00',
      value: 2
    },
  ], []);

  const handleInstallationUpdate = React.useCallback((update: InstallationUpdate) => {
    setCurrentProgress(update.progress);
    setTimeRemaining(update.estimatedTimeRemaining);

    const newEvent: InstallationTimelineEvent = {
      id: crypto.randomUUID(),
      type: 'step_change',
      timestamp: update.lastUpdate,
      title: `تحديث خطوة التركيب: ${update.currentStep.name}`,
      description: `الحالة: ${update.currentStep.status}`,
      severity: update.currentStep.status === 'completed' ? 'success' : 
               update.currentStep.status === 'failed' ? 'error' :
               update.currentStep.status === 'delayed' ? 'warning' : 'info',
    };
    setTimelineEvents(prev => [newEvent, ...prev]);

    if (update.currentStep.status === 'delayed') {
      const delayInfo = {
        stepName: update.currentStep.name,
        delayMinutes: 30, // This would come from the actual update
        severity: 'warning' as const,
        reason: 'تأخير في وصول الفريق',
      };
      setDelays(prev => [...prev, delayInfo]);
    }
  }, []);

  const handleDismissDelay = React.useCallback((index: number) => {
    setDelays(prev => prev.filter((_, i) => i !== index));
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        متابعة التركيب #{installationId}
      </Typography>
      <InstallationConsumer
        installationId={installationId}
        onUpdate={handleInstallationUpdate}
      />
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <InstallationProgressChart
              progress={currentProgress}
              estimatedTimeRemaining={timeRemaining}
            />
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Stack spacing={2}>
            {delays.map((delay, index) => (
              <InstallationDelayAlert
                key={index}
                delay={delay}
                onClose={() => handleDismissDelay(index)}
              />
            ))}
          </Stack>
          <Paper sx={{ p: 2 }}>
            <InstallationTimeline events={timelineEvents} />
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <InstallationHeatmap data={heatmapData} />
        </Grid>
      </Grid>
    </Box>
  );
};