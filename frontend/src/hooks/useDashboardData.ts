import { useQuery } from 'react-query';
import { apiService } from '../services/api';
import { generateMockActivities } from '../utils/mockData';

export interface DashboardData {
  stats: {
    activeCustomers: number;
    newOrders: number;
    todayInspections: number;
    scheduledInstallations: number;
  };
  activities: Array<{
    id: number;
    type: string;
    title: string;
    description: string;
    timestamp: string;
    user: string;
  }>;
}

const fetchDashboardData = async (): Promise<DashboardData> => {
  // TODO: Replace with actual API call when backend is ready
  // const response = await apiService.dashboard.getData();
  // return response.data;

      // Generate random variations around base numbers
      const baseStats = {
        activeCustomers: 1000,
        newOrders: 100,
        todayInspections: 20,
        scheduledInstallations: 40,
      };

      // Random variation between -10% and +10%
      const addRandomVariation = (base: number) => {
        const variation = (Math.random() * 0.2 - 0.1) * base; // -10% to +10%
        return Math.round(base + variation);
      };

      // Mock data for development
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            stats: {
              activeCustomers: addRandomVariation(baseStats.activeCustomers),
              newOrders: addRandomVariation(baseStats.newOrders),
              todayInspections: addRandomVariation(baseStats.todayInspections),
              scheduledInstallations: addRandomVariation(baseStats.scheduledInstallations),
            },
            activities: generateMockActivities(8),
      });
    }, 1000);
  });
};

export const useDashboardData = () => {
  return useQuery<DashboardData, Error>('dashboardData', fetchDashboardData, {
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });
};
