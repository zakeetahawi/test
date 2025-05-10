import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { DashboardPage } from '../DashboardPage';
import { dashboardService } from '../../../services/dashboardService';

vi.mock('../../../services/dashboardService', () => ({
  dashboardService: {
    getDashboardStats: vi.fn(),
  },
}));

const mockStats = {
  totalCustomers: 150,
  totalOrders: 75,
  totalRevenue: 50000,
  pendingInstallations: 12,
  inventoryValue: 75000,
  pendingInspections: 8,
  revenueData: {
    labels: ['يناير', 'فبراير', 'مارس'],
    data: [10000, 15000, 20000],
  },
  ordersData: {
    labels: ['يناير', 'فبراير', 'مارس'],
    data: [20, 25, 30],
  },
};

describe('DashboardPage', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  beforeEach(() => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(mockStats);
  });

  const renderDashboard = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <DashboardPage />
      </QueryClientProvider>
    );
  };

  it('renders loading state initially', async () => {
    vi.mocked(dashboardService.getDashboardStats).mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve(mockStats), 100))
    );
    
    renderDashboard();
    expect(screen.getByText(/جاري التحميل/i)).toBeInTheDocument();
  });

  it('renders all stat cards with correct values', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument();
      expect(screen.getByText('75')).toBeInTheDocument();
      // Using a regex to match the Arabic text with or without RTL marks
      expect(screen.getByText(/[‎]?٥٠٬٠٠٠ ر\.س\.?[‎]?/)).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText(/[‎]?٧٥٬٠٠٠ ر\.س\.?[‎]?/)).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
    });
  });

  it('renders charts with correct titles', async () => {
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText('الإيرادات الشهرية')).toBeInTheDocument();
      expect(screen.getByText('الطلبات الشهرية')).toBeInTheDocument();
    });
  });
});