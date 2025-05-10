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
  ChartOptions
} from 'chart.js';

// Register ChartJS components
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

export const lineChartOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      type: 'category',
      display: true,
      grid: {
        display: false
      }
    },
    y: {
      beginAtZero: true,
      grid: {
        drawBorder: false
      }
    }
  },
  plugins: {
    legend: {
      display: false
    }
  }
};

export const barChartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      type: 'category',
      display: true,
      grid: {
        display: false
      }
    },
    y: {
      beginAtZero: true,
      grid: {
        drawBorder: false
      }
    }
  },
  plugins: {
    legend: {
      display: false
    }
  }
};
