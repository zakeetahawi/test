import React from 'react';
import { Paper, Box, Typography } from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// تسجيل مكونات الرسم البياني
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface DashboardChartProps {
  data: {
    labels: string[];
    customers: number[];
    orders: number[];
    revenue: number[];
  };
}

const DashboardChart: React.FC<DashboardChartProps> = ({ data }) => {
  const options = {
    responsive: true,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    scales: {
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
      },
    },
    plugins: {
      legend: {
        position: 'top' as const,
        rtl: true,
        labels: {
          font: {
            family: 'Cairo'
          }
        }
      },
    },
  };

  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: 'العملاء',
        data: data.customers,
        borderColor: '#1976d2',
        backgroundColor: '#1976d215',
        yAxisID: 'y',
        tension: 0.4,
      },
      {
        label: 'الطلبات',
        data: data.orders,
        borderColor: '#9c27b0',
        backgroundColor: '#9c27b015',
        yAxisID: 'y',
        tension: 0.4,
      },
      {
        label: 'الإيرادات',
        data: data.revenue,
        borderColor: '#2e7d32',
        backgroundColor: '#2e7d3215',
        yAxisID: 'y',
        tension: 0.4,
      },
    ],
  };

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        تحليل الأداء
      </Typography>
      <Box sx={{ height: 350 }}>
        <Line options={options} data={chartData} />
      </Box>
    </Paper>
  );
};

export default DashboardChart;