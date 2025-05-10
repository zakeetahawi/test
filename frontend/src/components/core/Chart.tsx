import { FC } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler,
} from 'chart.js';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
import { Box, Paper, Typography, useTheme } from '@mui/material';

// تسجيل المكونات المطلوبة من Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

type ChartType = 'line' | 'bar' | 'pie' | 'doughnut';

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string;
    fill?: boolean;
  }[];
}

interface ChartProps {
  type: ChartType;
  data: ChartData;
  title?: string;
  height?: number;
  loading?: boolean;
  rtl?: boolean;
}

const Chart: FC<ChartProps> = ({
  type,
  data,
  title,
  height = 300,
  loading = false,
  rtl = true,
}) => {
  const theme = useTheme();

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    rtl,
    plugins: {
      legend: {
        position: rtl ? 'left' : 'right' as const,
        rtl,
      },
      title: {
        display: !!title,
        text: title,
        rtl,
      },
    },
    scales: type === 'line' || type === 'bar'
      ? {
          x: {
            reverse: rtl,
            grid: {
              display: false,
            },
          },
          y: {
            beginAtZero: true,
            grid: {
              color: theme.palette.divider,
            },
          },
        }
      : undefined,
  };

  const renderChart = () => {
    switch (type) {
      case 'line':
        return <Line data={data} options={options} />;
      case 'bar':
        return <Bar data={data} options={options} />;
      case 'pie':
        return <Pie data={data} options={options} />;
      case 'doughnut':
        return <Doughnut data={data} options={options} />;
      default:
        return null;
    }
  };

  return (
    <Paper sx={{ p: 2, height }}>
      {loading ? (
        <Box
          sx={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography variant="body1" color="textSecondary">
            جاري تحميل البيانات...
          </Typography>
        </Box>
      ) : (
        renderChart()
      )}
    </Paper>
  );
};

export default Chart;