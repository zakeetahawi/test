import { Card, CardContent, CardHeader } from '@mui/material';
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
  ChartData,
  ChartOptions
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface DashboardChartProps {
  title: string;
  data: ChartData<'line' | 'bar'>;
  type: 'line' | 'bar';
  height?: number;
  options?: ChartOptions<'line' | 'bar'>;
}

export const DashboardChart = ({ 
  title, 
  data, 
  type = 'line',
  height = 350,
  options 
}: DashboardChartProps) => {
  const defaultOptions: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        align: 'end' as const,
        rtl: true,
        labels: {
          boxWidth: 10,
          usePointStyle: true,
          pointStyle: 'circle',
        },
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        position: 'right' as const,
      },
    },
  };

  return (
    <Card>
      <CardHeader title={title} />
      <CardContent>
        <div style={{ height }}>
          {type === 'line' ? (
            <Line data={data} options={{ ...defaultOptions, ...options }} />
          ) : (
            <Bar data={data} options={{ ...defaultOptions, ...options }} />
          )}
        </div>
      </CardContent>
    </Card>
  );
};