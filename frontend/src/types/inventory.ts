export interface Product {
  id: number;
  code: string;
  name: string;
  description?: string;
  category: string;
  unit: string;
  price: number;
  stock: number;
  minStock: number;
  maxStock: number;
  status: 'active' | 'inactive';
}

export interface ProductFormData extends Omit<Product, 'id'> {}

export interface InventoryTransaction {
  id: number;
  productId: number;
  type: 'in' | 'out';
  quantity: number;
  date: string;
  reference: string;
  notes?: string;
  createdBy: string;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
  productsCount: number;
}

export interface ProductFilters {
  search?: string;
  category?: string;
  status?: string;
  stockStatus?: 'all' | 'low' | 'out';
  page: number;
  limit: number;
}

export interface StockStatus {
  totalProducts: number;
  lowStockProducts: number;
  outOfStockProducts: number;
  totalValue: number;
}