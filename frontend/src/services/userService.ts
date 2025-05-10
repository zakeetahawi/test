// filepath: d:\CRMsystem\frontend\src\services\userService.ts
import axios from 'axios';
import { User, UserCreateRequest, UserUpdateRequest } from '../types/user';

export interface UserListParams {
  page?: number;
  size?: number;
  search?: string;
  role?: string;
  isActive?: boolean;
}

const userService = {
  /**
   * جلب قائمة المستخدمين مع دعم التصفية والبحث والترقيم
   */
  async getUsers(params: UserListParams = {}): Promise<{
    users: User[];
    total: number;
    pages: number;
  }> {
    const response = await axios.get('/api/users/', { params });
    return response.data;
  },

  /**
   * جلب بيانات مستخدم محدد
   */
  async getUser(id: number | string): Promise<User> {
    const response = await axios.get(`/api/users/${id}/`);
    return response.data;
  },

  /**
   * إنشاء مستخدم جديد
   */
  async createUser(user: UserCreateRequest): Promise<User> {
    const response = await axios.post('/api/users/', user);
    return response.data;
  },

  /**
   * تحديث بيانات مستخدم
   */
  async updateUser(id: number | string, userData: UserUpdateRequest): Promise<User> {
    const response = await axios.patch(`/api/users/${id}/`, userData);
    return response.data;
  },

  /**
   * حذف مستخدم
   */
  async deleteUser(id: number | string): Promise<void> {
    await axios.delete(`/api/users/${id}/`);
  },

  /**
   * تفعيل أو إلغاء تفعيل مستخدم
   */
  async toggleUserStatus(id: number | string, isActive: boolean): Promise<User> {
    const response = await axios.patch(`/api/users/${id}/`, { is_active: isActive });
    return response.data;
  },

  /**
   * إعادة تعيين كلمة المرور للمستخدم
   */
  async resetPassword(id: number | string, newPassword: boolean = false): Promise<{ 
    message: string;
    temp_password?: string;
  }> {
    const response = await axios.post(`/api/users/${id}/reset-password/`, {
      generate_temp_password: newPassword
    });
    return response.data;
  },

  /**
   * جلب قائمة الأدوار المتاحة
   */
  async getRoles(): Promise<{ id: number; name: string; permissions: string[] }[]> {
    const response = await axios.get('/api/roles/');
    return response.data;
  }
};

export default userService;