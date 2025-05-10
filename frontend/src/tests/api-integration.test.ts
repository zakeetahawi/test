// filepath: d:\CRMsystem\frontend\src\tests\api-integration.test.ts
import { describe, it, expect } from 'vitest';
import { http } from 'msw';
import { server } from './mocks/server';

// اختبارات خدمات API
describe('خدمات API', () => {
  // اختبارات المصادقة
  describe('خدمة المصادقة', () => {
    it('يجب أن تعود استجابة تسجيل الدخول بالرموز المميزة الصحيحة', async () => {
      const response = await fetch('/api/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: 'admin', password: 'password' }),
      });

      const data = await response.json();
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('access');
      expect(data).toHaveProperty('refresh');
      expect(data.access).toBe('mock-access-token');
      expect(data.refresh).toBe('mock-refresh-token');
    });

    it('يجب أن تعالج تحديث الرمز المميز بشكل صحيح', async () => {
      const response = await fetch('/api/token/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: 'mock-refresh-token' }),
      });

      const data = await response.json();
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('access');
      expect(data.access).toBe('mock-new-access-token');
    });

    it('يجب أن ترجع خطأ عند فشل تسجيل الدخول', async () => {
      // تجاوز المعالج المحدد مسبقًا لاختبار سيناريو الخطأ
      server.use(
        http.post('/api/token/', () => {
          return new Response(JSON.stringify({ detail: 'بيانات اعتماد غير صحيحة' }), {
            status: 401,
            headers: {
              'Content-Type': 'application/json',
            },
          });
        })
      );

      const response = await fetch('/api/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: 'wrong', password: 'wrong' }),
      });

      const data = await response.json();
      expect(response.status).toBe(401);
      expect(data).toHaveProperty('detail');
      expect(data.detail).toBe('بيانات اعتماد غير صحيحة');
    });
  });

  // اختبارات بيانات لوحة التحكم
  describe('خدمة بيانات لوحة التحكم', () => {
    it('يجب أن تجلب إحصائيات لوحة التحكم بنجاح', async () => {
      const response = await fetch('/api/dashboard/stats/');
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('totalCustomers');
      expect(data).toHaveProperty('totalOrders');
      expect(data).toHaveProperty('totalRevenue');
      expect(data).toHaveProperty('revenueData');
      expect(data).toHaveProperty('ordersData');
      
      // التحقق من البيانات العربية
      expect(data.revenueData.labels).toContain('يناير');
      expect(data.revenueData.labels).toContain('فبراير');
      expect(data.revenueData.labels).toContain('مارس');
    });

    it('يجب أن تجلب النشاطات الأخيرة بنجاح', async () => {
      const response = await fetch('/api/dashboard/activities/');
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(Array.isArray(data)).toBe(true);
      expect(data.length).toBeGreaterThan(0);
      expect(data[0]).toHaveProperty('id');
      expect(data[0]).toHaveProperty('type');
      expect(data[0]).toHaveProperty('description');
      expect(data[0]).toHaveProperty('user');
      expect(data[0]).toHaveProperty('timestamp');
      
      // التحقق من البيانات العربية
      expect(data[0].user).toBe('محمد أحمد');
    });

    it('يجب أن تجلب الطلبات الأخيرة بنجاح', async () => {
      const response = await fetch('/api/dashboard/orders/');
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(Array.isArray(data)).toBe(true);
      expect(data.length).toBeGreaterThan(0);
      expect(data[0]).toHaveProperty('id');
      expect(data[0]).toHaveProperty('customerName');
      expect(data[0]).toHaveProperty('amount');
      expect(data[0]).toHaveProperty('date');
      expect(data[0]).toHaveProperty('status');
      
      // التحقق من البيانات العربية
      expect(data[0].customerName).toBe('شركة الأمل');
      expect(data[0].status).toBe('مكتمل');
    });

    it('يجب أن تجلب المهام النشطة بنجاح', async () => {
      const response = await fetch('/api/dashboard/tasks/');
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(Array.isArray(data)).toBe(true);
      expect(data.length).toBeGreaterThan(0);
      expect(data[0]).toHaveProperty('id');
      expect(data[0]).toHaveProperty('title');
      expect(data[0]).toHaveProperty('assignedTo');
      expect(data[0]).toHaveProperty('priority');
      expect(data[0]).toHaveProperty('dueDate');
      
      // التحقق من البيانات العربية
      expect(data[0].assignedTo).toBe('محمد أحمد');
      expect(data[0].priority).toBe('عالي');
    });

    it('يجب إرجاع خطأ عند فشل جلب إحصائيات لوحة التحكم', async () => {
      // تجاوز المعالج المحدد مسبقًا لاختبار سيناريو الخطأ
      server.use(
        http.get('/api/dashboard/stats/', () => {
          return new Response(JSON.stringify({ detail: 'فشل في الاتصال بالخادم' }), {
            status: 500,
            headers: {
              'Content-Type': 'application/json',
            },
          });
        })
      );

      const response = await fetch('/api/dashboard/stats/');
      const data = await response.json();
      
      expect(response.status).toBe(500);
      expect(data).toHaveProperty('detail');
    });
  });

  // اختبارات إدارة المستخدمين
  describe('خدمة إدارة المستخدمين', () => {
    it('يجب أن تجلب قائمة المستخدمين بنجاح', async () => {
      const response = await fetch('/api/users/');
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('users');
      expect(data).toHaveProperty('total');
      expect(data).toHaveProperty('pages');
      expect(Array.isArray(data.users)).toBe(true);
      expect(data.users.length).toBeGreaterThan(0);
      expect(data.users[0]).toHaveProperty('id');
      expect(data.users[0]).toHaveProperty('username');
      expect(data.users[0]).toHaveProperty('email');
      expect(data.users[0]).toHaveProperty('full_name');
      
      // التحقق من البيانات العربية
      expect(data.users[0].full_name).toBe('أحمد محمد');
    });

    it('يجب أن تدعم معلمات البحث والتصفية', async () => {
      const response = await fetch('/api/users/?search=سارة');
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(data.users.length).toBe(1);
      expect(data.users[0].full_name).toBe('سارة خالد');
    });

    it('يجب أن تجلب بيانات مستخدم محدد بنجاح', async () => {
      const response = await fetch('/api/users/1');
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('id');
      expect(data).toHaveProperty('username');
      expect(data).toHaveProperty('email');
      expect(data).toHaveProperty('full_name');
      expect(data.id).toBe(1);
      
      // التحقق من البيانات العربية
      expect(data.full_name).toBe('أحمد محمد');
    });

    it('يجب إرجاع خطأ عند طلب مستخدم غير موجود', async () => {
      const response = await fetch('/api/users/999');
      const data = await response.json();
      
      expect(response.status).toBe(404);
      expect(data).toHaveProperty('detail');
      expect(data.detail).toBe('المستخدم غير موجود');
    });

    it('يجب أن ينشئ مستخدم جديد بنجاح', async () => {
      const response = await fetch('/api/users/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'newuser',
          email: 'newuser@example.com',
          first_name: 'محمود',
          last_name: 'علي',
          role_id: 2,
          is_active: true,
        }),
      });
      
      const data = await response.json();
      
      expect(response.status).toBe(201);
      expect(data).toHaveProperty('id');
      expect(data).toHaveProperty('username');
      expect(data).toHaveProperty('email');
      expect(data.username).toBe('newuser');
      expect(data.email).toBe('newuser@example.com');
      
      // التحقق من البيانات العربية
      expect(data.first_name).toBe('محمود');
      expect(data.last_name).toBe('علي');
    });

    it('يجب أن يتعامل بشكل صحيح مع البيانات العربية', async () => {
      const response = await fetch('/api/users/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'arabic',
          email: 'arabic@example.com',
          first_name: 'محمد',
          last_name: 'العربي',
          role_id: 3,
          is_active: true,
        }),
      });
      
      const data = await response.json();
      
      expect(response.status).toBe(201);
      expect(data).toHaveProperty('id');
      expect(data.first_name).toBe('محمد');
      expect(data.last_name).toBe('العربي');
      expect(data.full_name).toBe('محمد العربي');
    });

    it('يجب إرجاع أخطاء التحقق عند إدخال بيانات مكررة', async () => {
      const response = await fetch('/api/users/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'existing',
          email: 'existing@example.com',
          first_name: 'موجود',
          last_name: 'مسبقا',
          role_id: 2,
          is_active: true,
        }),
      });
      
      const data = await response.json();
      
      expect(response.status).toBe(400);
      expect(data).toHaveProperty('username');
      expect(data).toHaveProperty('email');
      expect(Array.isArray(data.username)).toBe(true);
      expect(Array.isArray(data.email)).toBe(true);
      expect(data.username[0]).toBe('اسم المستخدم مستخدم بالفعل');
      expect(data.email[0]).toBe('البريد الإلكتروني مستخدم بالفعل');
    });

    it('يجب أن يقوم بتحديث بيانات مستخدم بنجاح', async () => {
      const response = await fetch('/api/users/2', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: 'سارة تم التعديل',
          role_id: 3,
        }),
      });
      
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('id');
      expect(data.id).toBe(2);
      expect(data.first_name).toBe('سارة تم التعديل');
      expect(data.role.id).toBe(3);
    });

    it('يجب أن يحذف مستخدم بنجاح', async () => {
      const response = await fetch('/api/users/2', {
        method: 'DELETE',
      });
      
      expect(response.status).toBe(204);
    });

    it('يجب أن يقوم بإعادة تعيين كلمة المرور بنجاح', async () => {
      const response = await fetch('/api/users/2/reset-password/', {
        method: 'POST',
      });
      
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('message');
      expect(data).toHaveProperty('temp_password');
      expect(data.message).toBe('تم إعادة تعيين كلمة المرور بنجاح');
    });

    it('يجب أن يجلب قائمة الأدوار بنجاح', async () => {
      const response = await fetch('/api/roles/');
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(Array.isArray(data)).toBe(true);
      expect(data.length).toBeGreaterThan(0);
      expect(data[0]).toHaveProperty('id');
      expect(data[0]).toHaveProperty('name');
      expect(data[0]).toHaveProperty('permissions');
      
      // التحقق من البيانات العربية
      expect(data[0].name).toBe('مدير');
    });
  });
});