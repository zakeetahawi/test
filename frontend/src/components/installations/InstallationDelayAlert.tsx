import React, { useEffect, useState } from 'react';
import { Box, Paper, Typography, Alert, AlertTitle, Collapse } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useTranslation } from 'react-i18next';
import { formatDistance } from 'date-fns';
import { ar } from 'date-fns/locale';

interface Step {
  id: number;
  name: string;
  estimated_duration: number;
  actual_duration?: number;
  start_time?: string;
  end_time?: string;
  is_completed: boolean;
}

interface Props {
  steps: Step[];
  startTime: string;
  delayThreshold: number; // بالدقائق
}

interface DelayInfo {
  step: Step;
  delayDuration: number;
  severity: 'warning' | 'error';
}

const InstallationDelayAlert: React.FC<Props> = ({ steps, startTime, delayThreshold }) => {
  const { t } = useTranslation();
  const theme = useTheme();
  const [delays, setDelays] = useState<DelayInfo[]>([]);
  const [showAlerts, setShowAlerts] = useState(true);

  useEffect(() => {
    // تحليل التأخيرات في الخطوات
    const currentDelays: DelayInfo[] = [];
    const now = new Date();
    let expectedTime = new Date(startTime);

    steps.forEach(step => {
      if (!step.is_completed && step.start_time) {
        const startDate = new Date(step.start_time);
        const elapsedMinutes = Math.floor((now.getTime() - startDate.getTime()) / (60 * 1000));
        
        if (elapsedMinutes > step.estimated_duration) {
          const delayDuration = elapsedMinutes - step.estimated_duration;
          currentDelays.push({
            step,
            delayDuration,
            severity: delayDuration > delayThreshold ? 'error' : 'warning'
          });
        }
      } else if (step.is_completed && step.start_time && step.end_time) {
        const actualDuration = step.actual_duration || 0;
        if (actualDuration > step.estimated_duration) {
          currentDelays.push({
            step,
            delayDuration: actualDuration - step.estimated_duration,
            severity: 'warning'
          });
        }
      }
      
      expectedTime = new Date(expectedTime.getTime() + (step.estimated_duration * 60 * 1000));
    });

    setDelays(currentDelays);
  }, [steps, startTime, delayThreshold]);

  if (delays.length === 0) return null;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          {t('تنبيهات التأخير')}
        </Typography>
        <Typography 
          variant="caption" 
          sx={{ 
            cursor: 'pointer',
            color: theme.palette.primary.main,
            '&:hover': {
              textDecoration: 'underline'
            }
          }}
          onClick={() => setShowAlerts(prev => !prev)}
        >
          {showAlerts ? t('إخفاء') : t('إظهار')}
        </Typography>
      </Box>

      <Collapse in={showAlerts}>
        {delays.map(({ step, delayDuration, severity }) => (
          <Alert 
            key={step.id} 
            severity={severity}
            sx={{ mb: 1 }}
          >
            <AlertTitle>
              {severity === 'error' ? t('تأخير كبير') : t('تأخير')} - {step.name}
            </AlertTitle>
            <Typography variant="body2">
              {t('مدة التأخير')}: {formatDistance(0, delayDuration * 60 * 1000, { locale: ar })}
            </Typography>
            {step.start_time && !step.is_completed && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                {t('بدأت منذ')}: {formatDistance(new Date(step.start_time), new Date(), {
                  addSuffix: true,
                  locale: ar
                })}
              </Typography>
            )}
          </Alert>
        ))}

        {delays.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {t('إجمالي التأخير')}: {formatDistance(0, delays.reduce((total, { delayDuration }) => 
                total + delayDuration, 0) * 60 * 1000, { locale: ar })}
            </Typography>
          </Box>
        )}
      </Collapse>
    </Paper>
  );
};

export default InstallationDelayAlert;
