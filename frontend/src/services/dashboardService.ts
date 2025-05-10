import axios from 'axios';

export interface DashboardStats {
  totalCustomers: number;
  totalOrders: number;
  totalRevenue: number;
  pendingInstallations: number;
  inventoryValue: number;
  pendingInspections: number;
  revenueData: {
    labels: string[];
    data: number[];
  };
  ordersData: {
    labels: string[];
    data: number[];
  };
}

export const dashboardService = {
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await axios.get('/api/dashboard/stats/');
    return response.data;
  }
};