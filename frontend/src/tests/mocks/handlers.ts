// filepath: d:\CRMsystem\frontend\src\tests\mocks\handlers.ts
import { http, HttpResponse } from 'msw';

// محاكاة بيانات المستخدمين
const users = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    first_name: 'أحمد',
    last_name: 'محمد',
    full_name: 'أحمد محمد',
    role: { id: 1, name: 'مدير', permissions: ['users.view', 'users.add', 'users.edit', 'users.delete'] },
    is_active: true,
    date_joined: '2025-01-01T10:00:00Z',
    last_login: '2025-05-01T08:30:00Z'
  },
  {
    id: 2,
    username: 'sarah',
    email: 'sarah@example.com',
    first_name: 'سارة',
    last_name: 'خالد',
    full_name: 'سارة خالد',
    role: { id: 2, name: 'مشرف', permissions: ['users.view', 'users.add'] },
    is_active: true,
    date_joined: '2025-02-15T11:20:00Z',
    last_login: '2025-05-01T09:45:00Z'
  },
  {
    id: 3,
    username: 'omar',
    email: 'omar@example.com',
    first_name: 'عمر',
    last_name: 'علي',
    full_name: 'عمر علي',
    role: { id: 3, name: 'موظف', permissions: ['users.view'] },
    is_active: true,
    date_joined: '2025-03-10T09:15:00Z',
    last_login: '2025-04-30T16:20:00Z'
  }
];

// محاكاة بيانات إحصائيات لوحة التحكم
const dashboardStats = {
  totalCustomers: 245,
  totalOrders: 1250,
  totalRevenue: 560000,
  revenueData: {
    labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو'],
    datasets: [
      {
        data: [45000, 52000, 49000, 60000, 42000]
      }
    ]
  },
  ordersData: {
    labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو'],
    datasets: [
      {
        data: [120, 150, 145, 165, 132]
      }
    ]
  }
};

// محاكاة بيانات النشاطات الأخيرة
const activities = [
  {
    id: 1,
    type: 'طلب',
    description: 'تم إنشاء طلب جديد #52',
    user: 'محمد أحمد',
    timestamp: '2025-05-05T09:30:00Z'
  },
  {
    id: 2,
    type: 'عميل',
    description: 'تم إضافة عميل جديد: شركة النور',
    user: 'سارة خالد',
    timestamp: '2025-05-05T11:20:00Z'
  },
  {
    id: 3,
    type: 'مهمة',
    description: 'تم إكمال مهمة: تقديم عرض سعر',
    user: 'عمر علي',
    timestamp: '2025-05-05T14:45:00Z'
  }
];

// محاكاة بيانات الطلبات الأخيرة
const orders = [
  {
    id: 101,
    customerName: 'شركة الأمل',
    amount: 5600,
    date: '2025-05-04T13:20:00Z',
    status: 'مكتمل'
  },
  {
    id: 102,
    customerName: 'مؤسسة الرياض',
    amount: 3200,
    date: '2025-05-04T10:15:00Z',
    status: 'قيد المعالجة'
  },
  {
    id: 103,
    customerName: 'شركة المستقبل',
    amount: 9500,
    date: '2025-05-03T15:40:00Z',
    status: 'مكتمل'
  }
];

// محاكاة بيانات المهام النشطة
const tasks = [
  {
    id: 201,
    title: 'متابعة العميل لتأكيد الطلب',
    assignedTo: 'محمد أحمد',
    priority: 'عالي',
    dueDate: '2025-05-08T17:00:00Z'
  },
  {
    id: 202,
    title: 'إعداد عرض سعر للعميل الجديد',
    assignedTo: 'سارة خالد',
    priority: 'متوسط',
    dueDate: '2025-05-10T12:00:00Z'
  },
  {
    id: 203,
    title: 'تحديث بيانات المخزون',
    assignedTo: 'عمر علي',
    priority: 'منخفض',
    dueDate: '2025-05-15T17:00:00Z'
  }
];

// تعريف معالجات MSW للاختبارات
export const handlers = [
  // معالجات المصادقة
  http.post('/api/token/', () => {
    return HttpResponse.json({
      access: 'mock-access-token',
      refresh: 'mock-refresh-token'
    }, { status: 200 });
  }),

  http.post('/api/token/refresh/', () => {
    return HttpResponse.json({
      access: 'mock-new-access-token'
    }, { status: 200 });
  }),

  // معالجات لوحة التحكم
  http.get('/api/dashboard/stats/', () => {
    return HttpResponse.json(dashboardStats, { status: 200 });
  }),

  http.get('/api/dashboard/activities/', () => {
    return HttpResponse.json(activities, { status: 200 });
  }),

  http.get('/api/dashboard/orders/', () => {
    return HttpResponse.json(orders, { status: 200 });
  }),

  http.get('/api/dashboard/tasks/', () => {
    return HttpResponse.json(tasks, { status: 200 });
  }),

  // معالجات المستخدمين
  http.get('/api/users/', ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get('search');
    
    if (search) {
      const filteredUsers = users.filter(
        user => user.full_name.includes(search) || 
                user.username.includes(search) || 
                user.email.includes(search)
      );
      
      return HttpResponse.json({
        users: filteredUsers,
        total: filteredUsers.length,
        pages: 1
      }, { status: 200 });
    }
    
    return HttpResponse.json({
      users: users,
      total: users.length,
      pages: 1
    }, { status: 200 });
  }),

  http.get('/api/users/:id', ({ params }) => {
    const id = Number(params.id);
    const user = users.find(u => u.id === id);
    
    if (!user) {
      return HttpResponse.json({
        detail: 'المستخدم غير موجود'
      }, { status: 404 });
    }
    
    return HttpResponse.json(user, { status: 200 });
  }),

  http.post('/api/users/', async ({ request }) => {
    const data = await request.json();
    
    if (data.username === 'existing') {
      return HttpResponse.json({
        username: ['اسم المستخدم مستخدم بالفعل'],
        email: ['البريد الإلكتروني مستخدم بالفعل']
      }, { status: 400 });
    }
    
    const newUser = {
      id: users.length + 1,
      ...data,
      full_name: `${data.first_name} ${data.last_name}`,
      role: { id: data.role_id, name: data.role_id === 1 ? 'مدير' : data.role_id === 2 ? 'مشرف' : 'موظف', permissions: [] },
      date_joined: new Date().toISOString(),
      last_login: null
    };
    
    return HttpResponse.json(newUser, { status: 201 });
  }),

  http.patch('/api/users/:id', async ({ params, request }) => {
    const id = Number(params.id);
    const data = await request.json();
    const user = users.find(u => u.id === id);
    
    if (!user) {
      return HttpResponse.json({
        detail: 'المستخدم غير موجود'
      }, { status: 404 });
    }
    
    const updatedUser = {
      ...user,
      ...data,
      full_name: data.first_name ? `${data.first_name} ${user.last_name}` : user.full_name,
      role: data.role_id ? 
        { id: data.role_id, name: data.role_id === 1 ? 'مدير' : data.role_id === 2 ? 'مشرف' : 'موظف', permissions: [] } : 
        user.role
    };
    
    return HttpResponse.json(updatedUser, { status: 200 });
  }),

  http.delete('/api/users/:id', () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.post('/api/users/:id/reset-password/', () => {
    return HttpResponse.json({
      message: 'تم إعادة تعيين كلمة المرور بنجاح',
      temp_password: 'Temp1234!'
    }, { status: 200 });
  }),

  // معالجات الأدوار
  http.get('/api/roles/', () => {
    return HttpResponse.json([
      { id: 1, name: 'مدير', permissions: ['users.*', 'customers.*', 'orders.*'] },
      { id: 2, name: 'مشرف', permissions: ['users.view', 'users.add', 'customers.*', 'orders.view'] },
      { id: 3, name: 'موظف', permissions: ['users.view', 'customers.view', 'orders.view'] }
    ], { status: 200 });
  })
];