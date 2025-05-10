import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { Chart as ChartJS, LinearScale, PointElement, Tooltip, Legend, ChartOptions } from 'chart.js';
import { Scatter } from 'react-chartjs-2';

ChartJS.register(LinearScale, PointElement, Tooltip, Legend);
import { useTranslation } from 'react-i18next';

interface Installation {
  id: number;
  status: string;
  scheduled_date: string;
  actual_start_date: string | null;
  actual_end_date: string | null;
}

interface Props {
  installations: Installation[];
  startDate: Date;
  endDate: Date;
}

const InstallationHeatmap: React.FC<Props> = ({ installations, startDate, endDate }) => {
  const { t } = useTranslation();
  const theme = useTheme();
  
  const days: Date[] = [];
  const currentDate = new Date(startDate);
  while (currentDate <= endDate) {
    days.push(new Date(currentDate));
    currentDate.setDate(currentDate.getDate() + 1);
  }

  const hours = Array.from({ length: 24 }, (_, i) => i);

  const data = {
    datasets: [{
      data: hours.flatMap(hour =>
        days.map(day => {
          const count = installations.filter(installation => {
            const installDate = new Date(installation.scheduled_date);
            return installDate.getDate() === day.getDate() &&
                   installDate.getMonth() === day.getMonth() &&
                   installDate.getHours() === hour;
          }).length;
          return {
            x: days.indexOf(day),
            y: hour,
            r: count * 5 + 5
          };
        })
      ),
      backgroundColor: theme.palette.primary.main,
      borderColor: theme.palette.background.paper,
      borderWidth: 1,
      pointStyle: 'circle'
    }]
  };

  const options: ChartOptions<'scatter'> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        type: 'linear',
        offset: true,
        min: -0.5,
        max: days.length - 0.5,
        ticks: {
          stepSize: 1,
          callback: (value) => {
            const index = typeof value === 'number' ? value : parseInt(value);
            const day = days[index];
            return day ? day.getDate().toString() : '';
          }
        },
        grid: {
          display: false
        }
      },
      y: {
        type: 'linear',
        offset: true,
        min: -0.5,
        max: 23.5,
        ticks: {
          stepSize: 1,
          callback: (value) => {
            const hour = typeof value === 'number' ? value : parseInt(value);
            return `${hour}:00`;
          }
        },
        grid: {
          display: false
        }
      }
    },
    plugins: {
      tooltip: {
        callbacks: {
          title() {
            return '';
          },
          label(context: any) {
            const data = context.raw as { x: number; y: number; r: number };
            const hour = data.y;
            const day = days[data.x].getDate();
            const count = Math.floor((data.r - 5) / 5);
            return `${day}/${days[data.x].getMonth() + 1} ${hour}:00 - ${count} ${t('تركيب')}`;
          }
        }
      },
      legend: {
        display: false
      }
    }
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom align="center">
        {t('توزيع عمليات التركيب')}
      </Typography>
      <Box sx={{ height: 400, width: '100%' }}>
        <Scatter data={data} options={options} />
      </Box>
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary" align="center">
          {t('إجمالي التركيبات')}: {installations.length}
        </Typography>
      </Box>
    </Paper>
  );
};

export default InstallationHeatmap;
