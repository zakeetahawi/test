import React, { useEffect, useState, useCallback } from 'react';
import { Box, Card, CardContent, Typography, LinearProgress, Grid, Chip, IconButton, Tooltip, Divider } from '@mui/material';
import InstallationProgressChart from './InstallationProgressChart';
import InstallationHeatmap from './InstallationHeatmap';
import InstallationTimePrediction from './InstallationTimePrediction';
import InstallationDelayAlert from './InstallationDelayAlert';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot
} from '@mui/lab';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  AccessTime as AccessTimeIcon,
  Star as StarIcon,
  Build as BuildIcon,
  Assignment as AssignmentIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { formatDate } from '../../utils/formatters';

interface InstallationStep {
  id: number;
  name: string;
  order: number;
  is_completed: boolean;
  completed_at: string | null;
}

interface QualityCheck {
  id: number;
  criteria: string;
  rating: number;
  created_at: string;
}

interface Issue {
  id: number;
  title: string;
  status: string;
  priority: string;
  created_at: string;
}

interface InstallationData {
  installation: {
    id: number;
    status: string;
    scheduled_date: string;
    actual_start_date: string | null;
    actual_end_date: string | null;
    quality_rating: number | null;
    notes: string;
  };
  team: {
    id: number;
    name: string;
    leader: {
      id: number;
      name: string;
    } | null;
  };
  order: {
    id: number;
    order_number: string;
  };
  steps: InstallationStep[];
  completion_percentage: number;
  quality_checks: QualityCheck[];
  issues: Issue[];
}

interface Props {
  installationId: number;
}

const InstallationTracker: React.FC<Props> = ({ installationId }) => {
  const { t } = useTranslation();
  const [data, setData] = useState<InstallationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  const getStatusColor = (status: string): 'warning' | 'info' | 'primary' | 'success' | 'error' | 'default' => {
    const colors: Record<string, 'warning' | 'info' | 'primary' | 'success' | 'error'> = {
      pending: 'warning',
      scheduled: 'info',
      in_progress: 'primary',
      completed: 'success',
      cancelled: 'error'
    };
    return colors[status] || 'default';
  };

  const getPriorityColor = (priority: string): 'success' | 'warning' | 'error' | 'default' => {
    const colors: Record<string, 'success' | 'warning' | 'error'> = {
      low: 'success',
      medium: 'warning',
      high: 'error',
      critical: 'error'
    };
    return colors[priority] || 'default';
  };

  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/installations/${installationId}/`);

    ws.onopen = () => {
      console.log('WebSocket Connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'initial_state') {
        setData(message.data);
      } else if (message.type === 'status_update') {
        setData(prevData => {
          if (!prevData) return null;
          return {
            ...prevData,
            installation: {
              ...prevData.installation,
              status: message.data.status
            }
          };
        });
      } else if (message.type === 'step_update') {
        setData(prevData => {
          if (!prevData) return null;
          return {
            ...prevData,
            steps: prevData.steps.map(step =>
              step.id === message.data.step_id
                ? { ...step, is_completed: message.data.is_completed }
                : step
            ),
            completion_percentage: message.data.completion_percentage
          };
        });
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setError(t('خطأ في الاتصال'));
    };

    ws.onclose = () => {
      console.log('WebSocket Disconnected');
      setTimeout(connectWebSocket, 3000); // إعادة الاتصال بعد 3 ثواني
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [installationId, t]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [connectWebSocket, socket]);

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!data) {
    return (
      <Box sx={{ p: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      {/* معلومات التركيب الأساسية */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6}>
              <Typography variant="h6">
                {t('طلب')} #{data.order.order_number}
              </Typography>
              <Typography color="textSecondary">
                {t('فريق التركيب')}: {data.team.name}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} sx={{ textAlign: 'right' }}>
              <Chip
                label={t(data.installation.status)}
                color={getStatusColor(data.installation.status)}
                sx={{ mb: 1 }}
              />
              {data.installation.quality_rating && (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                  {[...Array(5)].map((_, index) => (
                    <StarIcon
                      key={index}
                      sx={{
                        color: index < data.installation.quality_rating! ? 'primary.main' : 'grey.300'
                      }}
                    />
                  ))}
                </Box>
              )}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* نسبة الإكمال */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('نسبة الإكمال')}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box sx={{ width: '100%', mr: 1 }}>
              <LinearProgress
                variant="determinate"
                value={data.completion_percentage}
                sx={{ height: 10, borderRadius: 5 }}
              />
            </Box>
            <Box sx={{ minWidth: 35 }}>
              <Typography variant="body2" color="textSecondary">
                {`${Math.round(data.completion_percentage)}%`}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* خطوات التركيب */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('خطوات التركيب')}
          </Typography>
          <Timeline>
            {data.steps.map((step) => (
              <TimelineItem key={step.id}>
                <TimelineSeparator>
                  <TimelineDot color={step.is_completed ? 'success' : 'grey'}>
                    <BuildIcon />
                  </TimelineDot>
                  <TimelineConnector />
                </TimelineSeparator>
                <TimelineContent>
                  <Typography variant="subtitle1">{step.name}</Typography>
                  {step.completed_at && (
                    <Typography variant="caption" color="textSecondary">
                      {formatDate(step.completed_at)}
                    </Typography>
                  )}
                </TimelineContent>
              </TimelineItem>
            ))}
          </Timeline>
        </CardContent>
      </Card>

      {/* المشاكل النشطة */}
      {data.issues.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('المشاكل')}
            </Typography>
            {data.issues.map((issue) => (
              <Box key={issue.id} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <ErrorIcon color="error" sx={{ mr: 1 }} />
                  <Typography variant="subtitle1">{issue.title}</Typography>
                  <Chip
                    label={t(issue.priority)}
                    color={getPriorityColor(issue.priority)}
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Box>
                <Typography variant="caption" color="textSecondary">
                  {formatDate(issue.created_at)}
                </Typography>
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

      {/* التحليلات والتوقعات */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={6}>
          <InstallationProgressChart
            completionPercentage={data.completion_percentage}
            steps={data.steps}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <InstallationTimePrediction
            steps={data.steps.map(step => ({
              ...step,
              estimated_duration: 30, // مثال - يجب تحديث هذا من البيانات الفعلية
              actual_duration: step.is_completed ? 35 : undefined // مثال
            }))}
            startTime={data.installation.actual_start_date || data.installation.scheduled_date}
            currentStep={data.steps.findIndex(step => !step.is_completed)}
          />
        </Grid>
      </Grid>

      {/* تنبيهات التأخير */}
      <InstallationDelayAlert
        steps={data.steps.map(step => ({
          ...step,
          estimated_duration: 30, // مثال
          actual_duration: step.is_completed ? 35 : undefined, // مثال
          start_time: step.is_completed ? data.installation.actual_start_date : undefined,
          end_time: step.is_completed ? data.installation.actual_end_date : undefined
        }))}
        startTime={data.installation.actual_start_date || data.installation.scheduled_date}
        delayThreshold={60} // مثال - تأخير أكثر من ساعة يعتبر حرج
      />

      {/* خريطة حرارية للتركيبات */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <InstallationHeatmap
            installations={[{
              id: data.installation.id,
              status: data.installation.status,
              scheduled_date: data.installation.scheduled_date,
              actual_start_date: data.installation.actual_start_date,
              actual_end_date: data.installation.actual_end_date
            }]}
            startDate={new Date(data.installation.scheduled_date)}
            endDate={new Date(data.installation.actual_end_date || data.installation.scheduled_date)}
          />
        </CardContent>
      </Card>

      {/* فحوصات الجودة */}
      {data.quality_checks.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('فحوصات الجودة')}
            </Typography>
            <Grid container spacing={2}>
              {data.quality_checks.map((check) => (
                <Grid item xs={12} sm={6} key={check.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <AssignmentIcon sx={{ mr: 1 }} />
                    <Box>
                      <Typography variant="subtitle1">
                        {t(check.criteria)}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {[...Array(5)].map((_, index) => (
                          <StarIcon
                            key={index}
                            sx={{
                              color: index < check.rating ? 'primary.main' : 'grey.300',
                              fontSize: '1rem'
                            }}
                          />
                        ))}
                      </Box>
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default InstallationTracker;
