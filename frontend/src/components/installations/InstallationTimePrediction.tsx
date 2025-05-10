import React from 'react';
import { Box, Paper, Typography, LinearProgress } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useTranslation } from 'react-i18next';
import { formatDistance } from 'date-fns';
import { ar } from 'date-fns/locale';

interface Step {
  id: number;
  name: string;
  estimated_duration: number; // بالدقائق
  actual_duration?: number; // بالدقائق
  is_completed: boolean;
  start_time?: string;
}

interface Props {
  steps: Step[];
  startTime: string;
  currentStep?: number;
}

const InstallationTimePrediction: React.FC<Props> = ({ steps, startTime, currentStep }) => {
  const { t } = useTranslation();
  const theme = useTheme();

  // حساب الوقت المتوقع للإكمال
  const calculateEstimatedCompletion = () => {
    const startDate = new Date(startTime);
    const totalEstimatedMinutes = steps.reduce((total, step) => total + step.estimated_duration, 0);
    const estimatedEndDate = new Date(startDate.getTime() + totalEstimatedMinutes * 60 * 1000);
    
    // حساب الوقت المتبقي
    const now = new Date();
    const remainingTime = formatDistance(estimatedEndDate, now, {
      locale: ar,
      addSuffix: true
    });

    return {
      estimatedEndDate,
      remainingTime
    };
  };

  // حساب نسبة التقدم
  const calculateProgress = () => {
    const completedSteps = steps.filter(step => step.is_completed);
    const totalDuration = steps.reduce((total, step) => total + step.estimated_duration, 0);
    const completedDuration = completedSteps.reduce((total, step) => 
      total + (step.actual_duration || step.estimated_duration), 0);
    
    return (completedDuration / totalDuration) * 100;
  };

  const { estimatedEndDate, remainingTime } = calculateEstimatedCompletion();
  const progress = calculateProgress();

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom align="center">
        {t('توقعات إكمال التركيب')}
      </Typography>
      
      <Box sx={{ mt: 3 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {t('الوقت المتوقع للإكمال')}: {remainingTime}
        </Typography>
        
        <LinearProgress 
          variant="determinate" 
          value={progress}
          sx={{
            height: 10,
            borderRadius: 5,
            backgroundColor: theme.palette.grey[200],
            '& .MuiLinearProgress-bar': {
              borderRadius: 5,
              backgroundColor: theme.palette.primary.main,
            }
          }}
        />
        
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">
            {t('وقت البدء')}: {new Date(startTime).toLocaleTimeString('ar-EG')}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {t('الوقت المتوقع للانتهاء')}: {estimatedEndDate.toLocaleTimeString('ar-EG')}
          </Typography>
        </Box>
      </Box>

      <Box sx={{ mt: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          {t('تفاصيل الخطوات')}:
        </Typography>
        {steps.map((step, index) => (
          <Box key={step.id} sx={{ mt: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography 
                variant="body2"
                sx={{ 
                  color: step.is_completed 
                    ? theme.palette.success.main 
                    : currentStep === index 
                    ? theme.palette.primary.main 
                    : 'text.primary'
                }}
              >
                {step.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {step.actual_duration 
                  ? `${step.actual_duration} ${t('دقيقة')}`
                  : `${step.estimated_duration} ${t('دقيقة')} (${t('متوقع')})`}
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={step.is_completed ? 100 : currentStep === index ? 50 : 0}
              sx={{
                height: 4,
                mt: 0.5,
                borderRadius: 2,
                backgroundColor: theme.palette.grey[100],
                '& .MuiLinearProgress-bar': {
                  borderRadius: 2,
                  backgroundColor: step.is_completed 
                    ? theme.palette.success.main 
                    : theme.palette.primary.main,
                }
              }}
            />
          </Box>
        ))}
      </Box>
    </Paper>
  );
};

export default InstallationTimePrediction;
