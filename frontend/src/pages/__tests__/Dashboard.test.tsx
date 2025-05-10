// filepath: d:\CRMsystem\frontend\src\pages\__tests__\Dashboard.test.tsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import Dashboard from '../Dashboard';
import { useDashboard } from '../../hooks/useDashboard';

// Mock للـ hooks و services اللازمة
jest.mock('../../hooks/useDashboard');
jest.mock('chart.js');
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart" />,
  Bar: () => <div data-testid="bar-chart" />,
}));

const mockUseDashboard = useDashboard as jest.MockedFunction<typeof useDashboard>;

describe('Dashboard Component', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  // إعادة ضبط الـ mocks قبل كل اختبار
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('يعرض مؤشر التحميل عندما تكون البيانات قيد التحميل', () => {
    mockUseDashboard.mockReturnValue({
      stats: null,
      activities: null,
      orders: null,
      inventoryStatus: null,
      tasks: null,
      isLoading: true,
      error: null,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('يعرض رسالة الخطأ عندما يكون هناك خطأ', () => {
    const errorMessage = 'حدث خطأ في تحميل البيانات';
    mockUseDashboard.mockReturnValue({
      stats: null,
      activities: null,
      orders: null,
      inventoryStatus: null,
      tasks: null,
      isLoading: false,
      error: new Error(errorMessage),
    });

    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    );

    expect(screen.getByText(/حدث خطأ أثناء تحميل البيانات/)).toBeInTheDocument();
  });

  test('يعرض بيانات لوحة التحكم بشكل صحيح', async () => {
    // بيانات وهمية للاختبار
    const mockStats = {
      totalCustomers: 250,
      totalOrders: 125,
      totalRevenue: 500000,
      pendingInstallations: 15,
      inventoryValue: 300000,
      pendingInspections: 8,
      revenueData: {
        labels: ['يناير', 'فبراير', 'مارس'],
        data: [30000, 45000, 60000],
      },
      ordersData: {
        labels: ['يناير', 'فبراير', 'مارس'],
        data: [20, 25, 30],
      },
    };

    const mockOrders = [
      {
        id: 1,
        customerName: 'شركة الأمل',
        amount: 25000,
        date: '2025-05-01',
        status: 'مكتمل',
      },
      {
        id: 2,
        customerName: 'مؤسسة النور',
        amount: 30000,
        date: '2025-05-02',
        status: 'قيد المعالجة',
      },
    ];

    const mockTasks = [
      {
        id: 1,
        title: 'متابعة مع العميل حول التركيب',
        assignedTo: 'محمد أحمد',
        priority: 'عالي',
        dueDate: '2025-05-10',
      },
      {
        id: 2,
        title: 'مراجعة المخزون',
        assignedTo: 'سارة خالد',
        priority: 'متوسط',
        dueDate: '2025-05-15',
      },
    ];

    const mockActivities = [
      {
        id: 1,
        type: 'عميل',
        description: 'تم إضافة عميل جديد',
        user: 'محمد أحمد',
        timestamp: '2025-05-01T10:30:00',
      },
      {
        id: 2,
        type: 'طلب',
        description: 'تم تحديث حالة الطلب',
        user: 'سارة خالد',
        timestamp: '2025-05-02T11:45:00',
      },
    ];

    mockUseDashboard.mockReturnValue({
      stats: mockStats,
      activities: mockActivities,
      orders: mockOrders,
      inventoryStatus: null,
      tasks: mockTasks,
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    );

    // التحقق من عرض عناوين الأقسام
    expect(screen.getByText('لوحة التحكم')).toBeInTheDocument();
    expect(screen.getByText('الإيرادات الشهرية')).toBeInTheDocument();
    expect(screen.getByText('آخر الطلبات')).toBeInTheDocument();
    expect(screen.getByText('الطلبات الشهرية')).toBeInTheDocument();
    expect(screen.getByText('المهام النشطة')).toBeInTheDocument();
    expect(screen.getByText('آخر الأنشطة')).toBeInTheDocument();

    // التحقق من عرض بطاقات الإحصائيات
    expect(screen.getByText('العملاء')).toBeInTheDocument();
    expect(screen.getByText('250')).toBeInTheDocument();

    expect(screen.getByText('الطلبات')).toBeInTheDocument();
    expect(screen.getByText('125')).toBeInTheDocument();

    expect(screen.getByText('قيمة المخزون')).toBeInTheDocument();

    expect(screen.getByText('تركيبات معلقة')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();

    // التحقق من عرض بيانات الطلبات
    await waitFor(() => {
      expect(screen.getByText('شركة الأمل')).toBeInTheDocument();
      expect(screen.getByText('مؤسسة النور')).toBeInTheDocument();
    });

    // التحقق من عرض بيانات المهام
    await waitFor(() => {
      expect(screen.getByText('متابعة مع العميل حول التركيب')).toBeInTheDocument();
      expect(screen.getByText('مراجعة المخزون')).toBeInTheDocument();
    });

    // التحقق من عرض بيانات الأنشطة
    await waitFor(() => {
      expect(screen.getByText('تم إضافة عميل جديد')).toBeInTheDocument();
      expect(screen.getByText('تم تحديث حالة الطلب')).toBeInTheDocument();
    });
  });
});