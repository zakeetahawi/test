// filepath: d:\CRMsystem\frontend\src\pages\__tests__\UsersList.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { SnackbarProvider } from 'notistack';
import UsersList from '../UsersList';
import { 
  useUsers, 
  useRoles, 
  useDeleteUser, 
  useToggleUserStatus, 
  useResetPassword 
} from '../../hooks/useUsers';

// Mock للـ hooks اللازمة
jest.mock('../../hooks/useUsers');

const mockUseUsers = useUsers as jest.MockedFunction<typeof useUsers>;
const mockUseRoles = useRoles as jest.MockedFunction<typeof useRoles>;
const mockUseDeleteUser = useDeleteUser as jest.MockedFunction<typeof useDeleteUser>;
const mockUseToggleUserStatus = useToggleUserStatus as jest.MockedFunction<typeof useToggleUserStatus>;
const mockUseResetPassword = useResetPassword as jest.MockedFunction<typeof useResetPassword>;

describe('UsersList Component', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  // بيانات وهمية للمستخدمين
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
        last_login: '2023-05-01T10:30:00Z',
        permissions: ['admin'],
      },
      {
        id: 2,
        username: 'user',
        email: 'user@example.com',
        first_name: 'سارة',
        last_name: 'خالد',
        full_name: 'سارة خالد',
        role: { id: 2, name: 'مستخدم' },
        is_active: true,
        date_joined: '2023-02-01T00:00:00Z',
        last_login: '2023-05-02T11:45:00Z',
        permissions: ['view'],
      },
    ],
    total: 2,
    pages: 1,
  };

  const mockRoles = [
    { id: 1, name: 'مدير', permissions: [] },
    { id: 2, name: 'مستخدم', permissions: [] },
  ];

  // إعداد المحاكاة قبل كل اختبار
  beforeEach(() => {
    jest.clearAllMocks();

    mockUseUsers.mockReturnValue({
      data: mockUsers,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    } as any);

    mockUseRoles.mockReturnValue({
      data: mockRoles,
      isLoading: false,
      error: null,
    } as any);

    mockUseDeleteUser.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({}),
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    mockUseToggleUserStatus.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({}),
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    mockUseResetPassword.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({ 
        message: 'تم إعادة تعيين كلمة المرور بنجاح',
        temp_password: 'TempPass123'
      }),
      isLoading: false,
      isError: false,
      error: null,
    } as any);
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <SnackbarProvider>
          <MemoryRouter>
            <UsersList />
          </MemoryRouter>
        </SnackbarProvider>
      </QueryClientProvider>
    );
  };

  test('عرض قائمة المستخدمين بشكل صحيح', () => {
    renderComponent();

    // التحقق من عنوان الصفحة
    expect(screen.getByText('إدارة المستخدمين')).toBeInTheDocument();
    
    // التحقق من وجود زر إضافة مستخدم
    expect(screen.getByText('إضافة مستخدم')).toBeInTheDocument();
    
    // التحقق من عرض بيانات المستخدمين
    expect(screen.getByText('أحمد محمد')).toBeInTheDocument();
    expect(screen.getByText('(admin)')).toBeInTheDocument();
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    expect(screen.getByText('مدير')).toBeInTheDocument();
    
    expect(screen.getByText('سارة خالد')).toBeInTheDocument();
    expect(screen.getByText('(user)')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
    expect(screen.getByText('مستخدم')).toBeInTheDocument();
  });

  test('عرض مؤشر التحميل أثناء جلب البيانات', () => {
    mockUseUsers.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: jest.fn(),
    } as any);

    renderComponent();

    // التحقق من وجود مؤشر التحميل
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('عرض رسالة خطأ في حالة فشل جلب البيانات', () => {
    mockUseUsers.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('فشل في جلب بيانات المستخدمين'),
      refetch: jest.fn(),
    } as any);

    renderComponent();

    // التحقق من وجود رسالة الخطأ
    expect(screen.getByText(/فشل في جلب بيانات المستخدمين/)).toBeInTheDocument();
  });

  test('عرض رسالة عند عدم وجود بيانات', () => {
    mockUseUsers.mockReturnValue({
      data: { users: [], total: 0, pages: 0 },
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    } as any);

    renderComponent();

    // التحقق من وجود رسالة عدم وجود بيانات
    expect(screen.getByText('لا توجد بيانات للعرض')).toBeInTheDocument();
  });

  test('فتح نافذة تأكيد الحذف عند النقر على زر الحذف', () => {
    renderComponent();

    // النقر على زر حذف المستخدم الأول
    const deleteButtons = screen.getAllByLabelText('حذف');
    fireEvent.click(deleteButtons[0]);

    // التحقق من ظهور نافذة تأكيد الحذف
    expect(screen.getByText('تأكيد الحذف')).toBeInTheDocument();
    expect(screen.getByText(/هل أنت متأكد من رغبتك في حذف هذا المستخدم؟/)).toBeInTheDocument();
  });

  test('استدعاء وظيفة الحذف عند تأكيد الحذف', async () => {
    const mockDeleteAsync = jest.fn().mockResolvedValue({});
    mockUseDeleteUser.mockReturnValue({
      mutateAsync: mockDeleteAsync,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    renderComponent();

    // النقر على زر حذف المستخدم الأول
    const deleteButtons = screen.getAllByLabelText('حذف');
    fireEvent.click(deleteButtons[0]);

    // تأكيد الحذف
    fireEvent.click(screen.getByText('حذف'));

    // التحقق من استدعاء وظيفة الحذف بالمعرف الصحيح
    await waitFor(() => {
      expect(mockDeleteAsync).toHaveBeenCalledWith(1); // معرف المستخدم الأول
    });
  });

  test('فتح نافذة إعادة تعيين كلمة المرور عند النقر على زر إعادة التعيين', () => {
    renderComponent();

    // النقر على زر إعادة تعيين كلمة المرور للمستخدم الأول
    const resetButtons = screen.getAllByLabelText('إعادة تعيين كلمة المرور');
    fireEvent.click(resetButtons[0]);

    // التحقق من ظهور نافذة إعادة تعيين كلمة المرور
    expect(screen.getByText('إعادة تعيين كلمة المرور')).toBeInTheDocument();
    expect(screen.getByText(/هل ترغب في إعادة تعيين كلمة المرور/)).toBeInTheDocument();
  });

  test('عرض كلمة المرور المؤقتة بعد إعادة التعيين', async () => {
    const mockResetAsync = jest.fn().mockResolvedValue({ 
      message: 'تم إعادة تعيين كلمة المرور بنجاح',
      temp_password: 'TempPass123'
    });
    
    mockUseResetPassword.mockReturnValue({
      mutateAsync: mockResetAsync,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    renderComponent();

    // النقر على زر إعادة تعيين كلمة المرور للمستخدم الأول
    const resetButtons = screen.getAllByLabelText('إعادة تعيين كلمة المرور');
    fireEvent.click(resetButtons[0]);

    // تأكيد إعادة التعيين
    fireEvent.click(screen.getByText('إعادة تعيين'));

    // التحقق من استدعاء وظيفة إعادة التعيين بالمعلومات الصحيحة
    await waitFor(() => {
      expect(mockResetAsync).toHaveBeenCalledWith({
        id: 1, // معرف المستخدم الأول
        generateTemp: true
      });
    });

    // التحقق من عرض كلمة المرور المؤقتة
    await waitFor(() => {
      expect(screen.getByText('TempPass123')).toBeInTheDocument();
    });
  });

  test('تنقيح قائمة المستخدمين باستخدام البحث', () => {
    const mockRefetch = jest.fn();
    mockUseUsers.mockReturnValue({
      data: mockUsers,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    } as any);

    renderComponent();

    // إدخال نص البحث
    const searchInput = screen.getByPlaceholderText(/البحث بالاسم، البريد الإلكتروني/);
    fireEvent.change(searchInput, { target: { value: 'admin' } });
    
    // التحقق من تغيير قيمة حقل البحث
    expect(searchInput).toHaveValue('admin');
  });
});