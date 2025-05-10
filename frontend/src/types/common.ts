// Common type definitions

// User related types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_staff: boolean;
  is_superuser: boolean;
  avatar?: string;
  last_login?: string;
  permissions?: string[];
}

// Customer related types
export interface Customer {
  id: number;
  code: string;
  name: string;
  phone: string;
  email?: string;
  address?: string;
  customer_type: 'individual' | 'company' | 'government';
  status: 'active' | 'inactive' | 'blocked';
  created_at: string;
  updated_at: string;
  branch: {
    id: number;
    name: string;
  };
}

// Order related types
export interface Order {
  id: number;
  order_number: string;
  customer: Customer;
  total_amount: number;
  status: 'pending' | 'processing' | 'completed' | 'cancelled';
  payment_status: 'unpaid' | 'partially_paid' | 'paid';
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface OrderItem {
  id: number;
  product: Product;
  quantity: number;
  unit_price: number;
  total_price: number;
}

// Product related types
export interface Product {
  id: number;
  code: string;
  name: string;
  description?: string;
  unit_price: number;
  stock_quantity: number;
  category: {
    id: number;
    name: string;
  };
  status: 'active' | 'inactive' | 'out_of_stock';
}

// Inspection related types
export interface Inspection {
  id: number;
  inspection_number: string;
  customer: Customer;
  scheduled_date: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  notes?: string;
  inspector: User;
  created_at: string;
  updated_at: string;
}

// Installation related types
export interface Installation {
  id: number;
  installation_number: string;
  customer: Customer;
  order: Order;
  scheduled_date: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  installer: User;
  notes?: string;
  created_at: string;
  updated_at: string;
}

// Pagination types
export interface PaginationParams {
  page: number;
  page_size: number;
  search?: string;
  ordering?: string;
  [key: string]: any;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// API response types
export interface ApiSuccessResponse<T> {
  data: T;
  message?: string;
}

export interface ApiErrorResponse {
  message: string;
  errors?: {
    [key: string]: string[];
  };
}

// Notification types
export interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  priority: 'normal' | 'high' | 'urgent';
  is_read: boolean;
  created_at: string;
  link?: string;
}

// Report types
export interface Report {
  id: number;
  title: string;
  type: string;
  format: 'pdf' | 'excel' | 'csv';
  parameters?: Record<string, any>;
  created_by: User;
  created_at: string;
  file_url?: string;
}

// Theme types
export type ThemeOption = 'default' | 'light-sky' | 'soft-pink' | 'fresh-mint' | 'calm-lavender' | 'warm-beige';

// Form field types
export interface SelectOption {
  value: string | number;
  label: string;
}

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'date' | 'textarea' | 'checkbox';
  required?: boolean;
  options?: SelectOption[];
  validation?: {
    required?: string;
    min?: number;
    max?: number;
    pattern?: {
      value: RegExp;
      message: string;
    };
  };
}
