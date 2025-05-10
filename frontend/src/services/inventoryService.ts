import api from './api';
import { Product, ProductFormData, Category, ProductFilters, InventoryTransaction, StockStatus } from '@/types/inventory';

const inventoryService = {
  // إدارة المنتجات
  getProducts: async (filters?: ProductFilters) => {
    const response = await api.get('/inventory/products', { params: filters });
    return response.data;
  },

  getProduct: async (id: number) => {
    const response = await api.get(`/inventory/products/${id}`);
    return response.data;
  },

  createProduct: async (data: ProductFormData) => {
    const response = await api.post('/inventory/products', data);
    return response.data;
  },

  updateProduct: async (id: number, data: ProductFormData) => {
    const response = await api.put(`/inventory/products/${id}`, data);
    return response.data;
  },

  deleteProduct: async (id: number) => {
    const response = await api.delete(`/inventory/products/${id}`);
    return response.data;
  },

  // إدارة الفئات
  getCategories: async () => {
    const response = await api.get('/inventory/categories');
    return response.data;
  },

  createCategory: async (data: Omit<Category, 'id' | 'productsCount'>) => {
    const response = await api.post('/inventory/categories', data);
    return response.data;
  },

  updateCategory: async (id: number, data: Omit<Category, 'id' | 'productsCount'>) => {
    const response = await api.put(`/inventory/categories/${id}`, data);
    return response.data;
  },

  deleteCategory: async (id: number) => {
    const response = await api.delete(`/inventory/categories/${id}`);
    return response.data;
  },

  // إدارة المعاملات
  getTransactions: async (productId?: number) => {
    const response = await api.get('/inventory/transactions', {
      params: { productId },
    });
    return response.data;
  },

  addTransaction: async (data: {
    productId: number;
    type: 'in' | 'out';
    quantity: number;
    reference: string;
    notes?: string;
  }) => {
    const response = await api.post('/inventory/transactions', data);
    return response.data;
  },

  // تحليلات المخزون
  getStockStatus: async (): Promise<StockStatus> => {
    const response = await api.get('/inventory/status');
    return response.data;
  },

  // تصدير البيانات
  exportInventory: async (filters: any) => {
    const response = await api.get('/inventory/export', {
      params: filters,
      responseType: 'blob',
    });
    return response.data;
  },
};

export default inventoryService;