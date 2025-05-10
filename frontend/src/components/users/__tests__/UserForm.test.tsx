// filepath: d:\CRMsystem\frontend\src\components\users\__tests__\UserForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from 'react-query';
import UserForm from '../UserForm';
import { useRoles } from '../../../hooks/useUsers';

// Mock للـ hooks اللازمة
jest.mock('../../../hooks/useUsers');

const mockUseRoles = useRoles as jest.MockedFunction<typeof useRoles>;

describe('UserForm Component', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const mockOnSubmit = jest.fn();
  const mockRoles = [
    { id: 1, name: 'مدير', permissions: [] },
    { id: 2, name: 'مشرف', permissions: [] },
    { id: 3, name: 'مستخدم', permissions: [] },
  ];

  // إعادة ضبط المحاكاة قبل كل اختبار
  beforeEach(() => {
    jest.clearAllMocks();
    mockOnSubmit.mockClear();
    mockUseRoles.mockReturnValue({
      data: mockRoles,
      isLoading: false,
      error: null,
    } as any);
  });

  test('عرض نموذج إضافة مستخدم جديد بشكل صحيح', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <UserForm onSubmit={mockOnSubmit} isLoading={false} />
      </QueryClientProvider>
    );

    // التحقق من وجود حقول النموذج الرئيسية
    expect(screen.getByLabelText(/اسم المستخدم/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/البريد الإلكتروني/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/كلمة المرور/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/تأكيد كلمة المرور/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/الاسم الأول/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/الاسم الأخير/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/الدور/i)).toBeInTheDocument();
    
    // التحقق من وجود زر الإضافة
    expect(screen.getByRole('button', { name: /إضافة مستخدم/i })).toBeInTheDocument();
    
    // التحقق من تحميل الأدوار في القائمة
    expect(mockUseRoles).toHaveBeenCalled();
  });

  test('عرض نموذج تعديل مستخدم موجود بشكل صحيح', () => {
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'محمد',
      last_name: 'أحمد',
      role: { id: 1, name: 'مدير' },
      is_active: true,
      date_joined: '2023-01-01T00:00:00Z',
      permissions: [],
    };

    render(
      <QueryClientProvider client={queryClient}>
        <UserForm user={mockUser} onSubmit={mockOnSubmit} isLoading={false} />
      </QueryClientProvider>
    );

    // التحقق من عدم وجود حقل اسم المستخدم عند التعديل (لا يمكن تغييره)
    expect(screen.queryByLabelText(/اسم المستخدم/i)).not.toBeInTheDocument();
    
    // التحقق من وجود بيانات المستخدم المحملة مسبقًا في النموذج
    expect(screen.getByLabelText(/البريد الإلكتروني/i)).toHaveValue(mockUser.email);
    expect(screen.getByLabelText(/الاسم الأول/i)).toHaveValue(mockUser.first_name);
    expect(screen.getByLabelText(/الاسم الأخير/i)).toHaveValue(mockUser.last_name);
    
    // التحقق من وجود زر الحفظ بدلاً من زر الإضافة
    expect(screen.getByRole('button', { name: /حفظ التغييرات/i })).toBeInTheDocument();
  });

  test('التحقق من إرسال بيانات إنشاء مستخدم جديد بشكل صحيح', async () => {
    const user = userEvent.setup();
    
    render(
      <QueryClientProvider client={queryClient}>
        <UserForm onSubmit={mockOnSubmit} isLoading={false} />
      </QueryClientProvider>
    );

    // إدخال البيانات في النموذج
    await user.type(screen.getByLabelText(/اسم المستخدم/i), 'newuser');
    await user.type(screen.getByLabelText(/البريد الإلكتروني/i), 'new@example.com');
    await user.type(screen.getByLabelText(/كلمة المرور/i), 'Password123');
    await user.type(screen.getByLabelText(/تأكيد كلمة المرور/i), 'Password123');
    await user.type(screen.getByLabelText(/الاسم الأول/i), 'سارة');
    await user.type(screen.getByLabelText(/الاسم الأخير/i), 'خالد');
    
    // اختيار الدور
    fireEvent.mouseDown(screen.getByLabelText(/الدور/i));
    fireEvent.click(screen.getByText('مدير'));
    
    // إرسال النموذج
    await user.click(screen.getByRole('button', { name: /إضافة مستخدم/i }));
    
    // التحقق من استدعاء وظيفة الإرسال بالبيانات الصحيحة
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(expect.objectContaining({
        username: 'newuser',
        email: 'new@example.com',
        password: 'Password123',
        first_name: 'سارة',
        last_name: 'خالد',
        role_id: 1,
        is_active: true
      }));
    });
  });

  test('عرض أخطاء التحقق بشكل صحيح عند تقديم بيانات غير صالحة', async () => {
    const user = userEvent.setup();
    
    render(
      <QueryClientProvider client={queryClient}>
        <UserForm onSubmit={mockOnSubmit} isLoading={false} />
      </QueryClientProvider>
    );

    // ترك الحقول فارغة وإرسال النموذج
    await user.click(screen.getByRole('button', { name: /إضافة مستخدم/i }));
    
    // التحقق من ظهور رسائل الخطأ
    await waitFor(() => {
      expect(screen.getByText(/اسم المستخدم مطلوب/i)).toBeInTheDocument();
      expect(screen.getByText(/البريد الإلكتروني مطلوب/i)).toBeInTheDocument();
      expect(screen.getByText(/كلمة المرور مطلوبة/i)).toBeInTheDocument();
      expect(screen.getByText(/الاسم الأول مطلوب/i)).toBeInTheDocument();
      expect(screen.getByText(/الاسم الأخير مطلوب/i)).toBeInTheDocument();
    });
    
    // التحقق من عدم استدعاء وظيفة الإرسال عند وجود أخطاء
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('تعطيل النموذج أثناء التحميل', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <UserForm onSubmit={mockOnSubmit} isLoading={true} />
      </QueryClientProvider>
    );
    
    // التحقق من تعطيل الحقول وزر الإرسال
    expect(screen.getByLabelText(/اسم المستخدم/i)).toBeDisabled();
    expect(screen.getByLabelText(/البريد الإلكتروني/i)).toBeDisabled();
    expect(screen.getByLabelText(/كلمة المرور/i)).toBeDisabled();
    expect(screen.getByRole('button')).toBeDisabled();
    
    // التحقق من وجود مؤشر التحميل
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});