import React, { useEffect, useRef } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);
import { useTranslation } from 'react-i18next';

interface Props {
  completionPercentage: number;
  steps: {
    name: string;
    is_completed: boolean;
    order: number;
  }[];
}

const InstallationProgressChart: React.FC<Props> = ({ completionPercentage, steps }) => {
  const { t } = useTranslation();
  const theme = useTheme();
  const completedSteps = steps.filter(step => step.is_completed).length;
  const totalSteps = steps.length;
  const remainingSteps = totalSteps - completedSteps;

  const data = {
    labels: [t('مكتمل'), t('متبقي')],
    datasets: [{
      data: [completedSteps, remainingSteps],
      backgroundColor: [
        theme.palette.success.main,
        theme.palette.grey[300]
      ],
      borderWidth: 0,
      hoverOffset: 4
    }]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '80%',
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        enabled: true,
        callbacks: {
          label: (context: any) => {
            const value = context.raw as number;
            const percentage = Math.round((value / totalSteps) * 100);
            return `${context.label}: ${value} (${percentage}%)`;
          }
        }
      }
    }
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom align="center">
        {t('تقدم التركيب')}
      </Typography>
      <Box sx={{ position: 'relative', height: 200, width: '100%' }}>
        <Doughnut data={data} options={options} />
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center'
          }}
        >
          <Typography variant="h4" color="primary">
            {Math.round(completionPercentage)}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('مكتمل')}
          </Typography>
        </Box>
      </Box>
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary" align="center">
          {t('الخطوات المكتملة')}: {steps.filter(step => step.is_completed).length}/{steps.length}
        </Typography>
      </Box>
    </Paper>
  );
};

export default InstallationProgressChart;
