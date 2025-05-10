// filepath: d:\CRMsystem\frontend\src\tests\component-integration.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from 'vitest';
import { ThemeProvider } from '@mui/material/styles';
import { theme } from '../theme';

// استيراد المكونات
import Dashboard from '../pages/Dashboard';
import UsersList from '../pages/UsersList';
import UserEdit from '../pages/UserEdit';
import DashboardPage from '../pages/DashboardPage';
import * as useUsers from '../hooks/useUsers';
import * as useDashboard from '../hooks/useDashboard';

// إعداد المخدم الوهمي للردود
const server = setupServer(
  // استجابة API لبيانات لوحة التحكم
  http.get('/api/dashboard/stats/', () => {
    return HttpResponse.json({
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
      }
    }, { status: 200 });
  }),

  http.get('/api/dashboard/activities/', () => {
    return HttpResponse.json([
      {
        id: 1,
        type: 'عميل',
        description: 'تم إضافة عميل جديد',
        user: 'محمد أحمد',
        timestamp: '2025-05-01T10:30:00Z',
      }
    ], { status: 200 });
  }),

  http.get('/api/dashboard/orders/', () => {
    return HttpResponse.json([
      {
        id: 1,
        customerName: 'شركة الأمل',
        amount: 25000,
        date: '2025-05-01',
        status: 'مكتمل',
      }
    ], { status: 200 });
  }),

  http.get('/api/dashboard/tasks/', () => {
    return HttpResponse.json([
      {
        id: 1,
        title: 'متابعة مع العميل',
        assignedTo: 'محمد أحمد',
        priority: 'عالي',
        dueDate: '2025-05-10',
      }
    ], { status: 200 });
  }),

  // استجابة API لإدارة المستخدمين
  http.get('/api/users/', () => {
    return HttpResponse.json({
      users: [
        {
          id: 1,
          username: 'admin',
          email: 'admin@example.com',
          first_name: 'أحمد',
          last_name: 'محمد',
          full_name: 'أحمد محمد',
          role: { id: 1, name: 'مدير' },
          is_active: true,
          date_joined: '2023-01-01T00:00:00Z',
          last_login: '2025-05-01T10:30:00Z',
          permissions: ['admin'],
        }
      ],
      total: 1,
      pages: 1,
    }, { status: 200 });
  }),

  http.get('/api/users/1/', () => {
    return HttpResponse.json({
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      first_name: 'أحمد',
      last_name: 'محمد',
      full_name: 'أحمد محمد',
      role: { id: 1, name: 'مدير' },
      is_active: true,
      date_joined: '2023-01-01T00:00:00Z',
      last_login: '2025-05-01T10:30:00Z',
      permissions: ['admin'],
    }, { status: 200 });
  }),

  http.delete('/api/users/1/', () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.patch('/api/users/1/', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: 1,
      username: 'admin',
      email: body.email || 'admin@example.com',
      first_name: body.first_name || 'أحمد',
      last_name: body.last_name || 'محمد',
      full_name: `${body.first_name || 'أحمد'} ${body.last_name || 'محمد'}`,
      role: { id: body.role_id || 1, name: 'مدير' },
      is_active: body.is_active !== undefined ? body.is_active : true,
      date_joined: '2023-01-01T00:00:00Z',
      last_login: '2025-05-01T10:30:00Z',
      permissions: ['admin'],
    }, { status: 200 });
  }),

  http.get('/api/roles/', () => {
    return HttpResponse.json([
      { id: 1, name: 'مدير', permissions: ['admin', 'edit', 'view'] },
      { id: 2, name: 'مشرف', permissions: ['edit', 'view'] },
      { id: 3, name: 'مستخدم', permissions: ['view'] },
    ], { status: 200 });
  })
);

// إعداد مكتبة الاختبار
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// إنشاء مزود QueryClient للاختبارات
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        {ui}
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('اختبارات تكامل المكونات مع API', () => {
  describe('مكون لوحة التحكم', () => {
    it('يجب عرض بيانات لوحة التحكم من API', async () => {
      // محاكاة استدعاء hook useDashboard
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
        }
      };

      const mockActivities = [
        {
          id: 1,
          type: 'عميل',
          description: 'تم إضافة عميل جديد',
          user: 'محمد أحمد',
          timestamp: '2025-05-01T10:30:00Z',
        }
      ];

      const mockOrders = [
        {
          id: 1,
          customerName: 'شركة الأمل',
          amount: 25000,
          date: '2025-05-01',
          status: 'مكتمل',
        }
      ];

      const mockTasks = [
        {
          id: 1,
          title: 'متابعة مع العميل',
          assignedTo: 'محمد أحمد',
          priority: 'عالي',
          dueDate: '2025-05-10',
        }
      ];

      // محاكاة hook useDashboard
      vi.spyOn(useDashboard, 'useDashboard').mockReturnValue({
        stats: mockStats,
        activities: mockActivities,
        orders: mockOrders,
        inventoryStatus: null,
        tasks: mockTasks,
        isLoading: false,
        error: null,
      });

      render(
        <QueryClientProvider client={createTestQueryClient()}>
          <Dashboard />
        </QueryClientProvider>
      );

      // انتظار ظهور البيانات في الواجهة
      await waitFor(() => {
        // التحقق من وجود بيانات الإحصائيات
        expect(screen.getByText('العملاء')).toBeInTheDocument();
        expect(screen.getByText('250')).toBeInTheDocument();
        expect(screen.getByText('الطلبات')).toBeInTheDocument();
        expect(screen.getByText('125')).toBeInTheDocument();
        
        // التحقق من وجود بيانات النشاطات
        expect(screen.getByText('تم إضافة عميل جديد')).toBeInTheDocument();
        
        // التحقق من وجود بيانات الطلبات
        expect(screen.getByText('شركة الأمل')).toBeInTheDocument();
        
        // التحقق من وجود بيانات المهام
        expect(screen.getByText('متابعة مع العميل')).toBeInTheDocument();
      });
    });

    it('يجب عرض مؤشر التحميل أثناء استدعاء البيانات من API', () => {
      // محاكاة حالة التحميل
      vi.spyOn(useDashboard, 'useDashboard').mockReturnValue({
        stats: null,
        activities: null,
        orders: null,
        inventoryStatus: null,
        tasks: null,
        isLoading: true,
        error: null,
      });

      render(
        <QueryClientProvider client={createTestQueryClient()}>
          <Dashboard />
        </QueryClientProvider>
      );

      // التحقق من وجود مؤشر التحميل
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('يجب عرض رسالة الخطأ عند فشل استدعاء البيانات من API', () => {
      // محاكاة خطأ في جلب البيانات
      vi.spyOn(useDashboard, 'useDashboard').mockReturnValue({
        stats: null,
        activities: null,
        orders: null,
        inventoryStatus: null,
        tasks: null,
        isLoading: false,
        error: new Error('فشل في جلب بيانات لوحة التحكم'),
      });

      render(
        <QueryClientProvider client={createTestQueryClient()}>
          <Dashboard />
        </QueryClientProvider>
      );

      // التحقق من وجود رسالة الخطأ
      expect(screen.getByText(/حدث خطأ أثناء تحميل البيانات/)).toBeInTheDocument();
    });
  });

  describe('DashboardPage', () => {
    it('يجب عرض حالة التحميل', () => {
      renderWithProviders(<DashboardPage />);
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('يجب عرض البيانات عند نجاح الطلب', async () => {
      const mockData = {
        customersCount: 150,
        ordersCount: 75,
        inventoryValue: 250000,
        pendingInstallations: 12,
        revenueChart: {
          labels: ['يناير', 'فبراير', 'مارس'],
          datasets: [{
            label: 'الإيرادات',
            data: [30000, 45000, 60000],
            borderColor: '#4caf50',
            fill: false
          }]
        },
        ordersChart: {
          labels: ['مكتمل', 'قيد التنفيذ', 'ملغي'],
          datasets: [{
            label: 'حالة الطلبات',
            data: [45, 20, 10],
            backgroundColor: ['#4caf50', '#ff9800', '#f44336']
          }]
        }
      };

      // Mock the API response
      jest.spyOn(global, 'fetch').mockImplementation(() =>
        Promise.resolve({
          json: () => Promise.resolve(mockData),
          ok: true
        } as Response)
      );

      renderWithProviders(<DashboardPage />);

      // Check if data is displayed
      expect(await screen.findByText('150')).toBeInTheDocument();
      expect(await screen.findByText('75')).toBeInTheDocument();
      expect(await screen.findByText('250,000 ج.م')).toBeInTheDocument();
      expect(await screen.findByText('12')).toBeInTheDocument();
    });

    it('يجب عرض رسالة خطأ عند فشل الطلب', async () => {
      // Mock API error
      jest.spyOn(global, 'fetch').mockImplementation(() =>
        Promise.reject(new Error('Failed to fetch'))
      );

      renderWithProviders(<DashboardPage />);

      expect(await screen.findByText('حدث خطأ أثناء تحميل البيانات')).toBeInTheDocument();
    });
  });

  describe('مكون قائمة المستخدمين', () => {
    it('يجب عرض قائمة المستخدمين من API', async () => {
      // محاكاة استدعاء hook useUsers
      const mockUsers = {
        users: [
          {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            first_name: 'أحمد',
            last_name: 'محمد',
            full_name: 'أحمد محمد',
            role: { id: 1, name: 'مدير' },
            is_active: true,
            date_joined: '2023-01-01T00:00:00Z',
            last_login: '2025-05-01T10:30:00Z',
            permissions: ['admin'],
          }
        ],
        total: 1,
        pages: 1,
      };

      const mockRoles = [
        { id: 1, name: 'مدير', permissions: ['admin', 'edit', 'view'] },
        { id: 2, name: 'مشرف', permissions: ['edit', 'view'] },
        { id: 3, name: 'مستخدم', permissions: ['view'] },
      ];

      // محاكاة hooks إدارة المستخدمين
      vi.spyOn(useUsers, 'useUsers').mockReturnValue({
        data: mockUsers,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      vi.spyOn(useUsers, 'useRoles').mockReturnValue({
        data: mockRoles,
        isLoading: false,
        error: null,
      } as any);

      vi.spyOn(useUsers, 'useDeleteUser').mockReturnValue({
        mutateAsync: vi.fn().mockResolvedValue({}),
        isLoading: false,
        isError: false,
        error: null,
      } as any);

      vi.spyOn(useUsers, 'useToggleUserStatus').mockReturnValue({
        mutateAsync: vi.fn().mockResolvedValue({}),
        isLoading: false,
        isError: false,
        error: null,
      } as any);

      render(
        <QueryClientProvider client={createTestQueryClient()}>
          <SnackbarProvider>
            <MemoryRouter>
              <UsersList />
            </MemoryRouter>
          </SnackbarProvider>
        </QueryClientProvider>
      );

      // انتظار ظهور البيانات في الواجهة
      await waitFor(() => {
        // التحقق من وجود معلومات المستخدم
        expect(screen.getByText('أحمد محمد')).toBeInTheDocument();
        expect(screen.getByText('(admin)')).toBeInTheDocument();
        expect(screen.getByText('admin@example.com')).toBeInTheDocument();
        expect(screen.getByText('مدير')).toBeInTheDocument();
        
        // التحقق من وجود أزرار الإجراءات
        expect(screen.getByLabelText('تعديل')).toBeInTheDocument();
        expect(screen.getByLabelText('حذف')).toBeInTheDocument();
      });
    });

    it('يجب استدعاء وظيفة الحذف عند النقر على زر الحذف وتأكيد الإجراء', async () => {
      // إعداد المستخدمين لاختبار الحذف
      const mockUsers = {
        users: [
          {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            first_name: 'أحمد',
            last_name: 'محمد',
            full_name: 'أحمد محمد',
            role: { id: 1, name: 'مدير' },
            is_active: true,
            date_joined: '2023-01-01T00:00:00Z',
            last_login: '2025-05-01T10:30:00Z',
            permissions: ['admin'],
          }
        ],
        total: 1,
        pages: 1,
      };

      // محاكاة وظيفة الحذف
      const mockDeleteAsync = vi.fn().mockResolvedValue({});
      
      // محاكاة hooks المطلوبة
      vi.spyOn(useUsers, 'useUsers').mockReturnValue({
        data: mockUsers,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);
      
      vi.spyOn(useUsers, 'useRoles').mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as any);
      
      vi.spyOn(useUsers, 'useDeleteUser').mockReturnValue({
        mutateAsync: mockDeleteAsync,
        isLoading: false,
        isError: false,
        error: null,
      } as any);

      // تقديم المكون
      render(
        <QueryClientProvider client={createTestQueryClient()}>
          <SnackbarProvider>
            <MemoryRouter>
              <UsersList />
            </MemoryRouter>
          </SnackbarProvider>
        </QueryClientProvider>
      );

      // انتظار ظهور البيانات
      await waitFor(() => {
        expect(screen.getByText('أحمد محمد')).toBeInTheDocument();
      });

      // النقر على زر الحذف
      fireEvent.click(screen.getByLabelText('حذف'));
      
      // التحقق من ظهور مربع الحوار
      expect(screen.getByText('تأكيد الحذف')).toBeInTheDocument();
      
      // تأكيد الحذف
      fireEvent.click(screen.getByRole('button', { name: /حذف/ }));
      
      // التحقق من استدعاء وظيفة الحذف بالمعرف الصحيح
      await waitFor(() => {
        expect(mockDeleteAsync).toHaveBeenCalledWith(1);
      });
    });
  });

  describe('مكون تعديل المستخدم', () => {
    it('يجب عرض بيانات المستخدم للتعديل من API', async () => {
      // محاكاة المستخدم للتعديل
      const mockUser = {
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        first_name: 'أحمد',
        last_name: 'محمد',
        full_name: 'أحمد محمد',
        role: { id: 1, name: 'مدير' },
        is_active: true,
        date_joined: '2023-01-01T00:00:00Z',
        last_login: '2025-05-01T10:30:00Z',
        permissions: ['admin'],
      };

      // محاكاة الأدوار
      const mockRoles = [
        { id: 1, name: 'مدير', permissions: ['admin'] },
        { id: 2, name: 'مستخدم', permissions: ['view'] },
      ];

      // محاكاة وظيفة التحديث
      const mockUpdateAsync = vi.fn().mockResolvedValue({
        ...mockUser,
        email: 'updated@example.com',
      });

      // محاكاة hooks المطلوبة
      vi.spyOn(useUsers, 'useUser').mockReturnValue({
        data: mockUser,
        isLoading: false,
        error: null,
      } as any);
      
      vi.spyOn(useUsers, 'useRoles').mockReturnValue({
        data: mockRoles,
        isLoading: false,
        error: null,
      } as any);
      
      vi.spyOn(useUsers, 'useUpdateUser').mockReturnValue({
        mutateAsync: mockUpdateAsync,
        isLoading: false,
        isError: false,
        error: null,
      } as any);

      // تقديم المكون مع مسار يحتوي على معرف المستخدم
      render(
        <QueryClientProvider client={createTestQueryClient()}>
          <SnackbarProvider>
            <MemoryRouter initialEntries={['/users/edit/1']}>
              <Routes>
                <Route path="/users/edit/:id" element={<UserEdit />} />
              </Routes>
            </MemoryRouter>
          </SnackbarProvider>
        </QueryClientProvider>
      );

      // انتظار ظهور البيانات
      await waitFor(() => {
        // التحقق من وجود معلومات المستخدم في النموذج
        expect(screen.getByDisplayValue('admin@example.com')).toBeInTheDocument();
        expect(screen.getByDisplayValue('أحمد')).toBeInTheDocument();
        expect(screen.getByDisplayValue('محمد')).toBeInTheDocument();
      });

      // تعديل البريد الإلكتروني
      fireEvent.change(screen.getByLabelText(/البريد الإلكتروني/i), {
        target: { value: 'updated@example.com' },
      });

      // تقديم النموذج
      fireEvent.click(screen.getByRole('button', { name: /حفظ التغييرات/i }));

      // التحقق من استدعاء وظيفة التحديث بالبيانات الصحيحة
      await waitFor(() => {
        expect(mockUpdateAsync).toHaveBeenCalledWith(expect.objectContaining({
          email: 'updated@example.com',
        }));
      });
    });

    it('يجب عرض مؤشر التحميل عند جلب بيانات المستخدم', () => {
      // محاكاة حالة التحميل
      vi.spyOn(useUsers, 'useUser').mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      } as any);
      
      vi.spyOn(useUsers, 'useUpdateUser').mockReturnValue({
        mutateAsync: vi.fn(),
        isLoading: false,
        isError: false,
        error: null,
      } as any);

      // تقديم المكون
      render(
        <QueryClientProvider client={createTestQueryClient()}>
          <SnackbarProvider>
            <MemoryRouter initialEntries={['/users/edit/1']}>
              <Routes>
                <Route path="/users/edit/:id" element={<UserEdit />} />
              </Routes>
            </MemoryRouter>
          </SnackbarProvider>
        </QueryClientProvider>
      );

      // التحقق من وجود مؤشر التحميل
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('يجب عرض رسالة خطأ عند فشل جلب بيانات المستخدم', () => {
      // محاكاة حالة الخطأ
      vi.spyOn(useUsers, 'useUser').mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('فشل في جلب بيانات المستخدم'),
      } as any);
      
      vi.spyOn(useUsers, 'useUpdateUser').mockReturnValue({
        mutateAsync: vi.fn(),
        isLoading: false,
        isError: false,
        error: null,
      } as any);

      // تقديم المكون
      render(
        <QueryClientProvider client={createTestQueryClient()}>
          <SnackbarProvider>
            <MemoryRouter initialEntries={['/users/edit/1']}>
              <Routes>
                <Route path="/users/edit/:id" element={<UserEdit />} />
              </Routes>
            </MemoryRouter>
          </SnackbarProvider>
        </QueryClientProvider>
      );

      // التحقق من وجود رسالة الخطأ
      expect(screen.getByText(/خطأ في جلب بيانات المستخدم/)).toBeInTheDocument();
    });
  });
});