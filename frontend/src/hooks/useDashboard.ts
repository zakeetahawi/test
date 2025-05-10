import { useQuery } from 'react-query';
import { api } from '../services/api';

interface ChartData {
  labels: string[];
  data: number[];
}

export interface DashboardData {
  stats: {
    totalCustomers: number;
    totalOrders: number;
    totalInventory: number;
    totalInstallations: number;
  };
  charts: {
    monthlySales: ChartData;
    orderDistribution: ChartData;
  };
  activities: Array<{
    id: string;
    title: string;
    timestamp: string;
  }>;
}

export const useDashboard = () => {
  return useQuery<DashboardData>(
    'dashboard',
    async () => {
      const { data } = await api.get('/api/dashboard/');
      return data;
    },
    {
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000
    }
  );
};
