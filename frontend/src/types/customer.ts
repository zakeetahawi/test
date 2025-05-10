export interface Customer {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  company?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
  status: 'active' | 'inactive';
  type: 'individual' | 'company';
}

export interface CustomerType {
  id: number;
  name: string;
  code: string;
  phone: string;
  email?: string;
  address?: string;
  customer_type: 'individual' | 'company' | 'government';
  status: 'active' | 'inactive' | 'blocked';
  category?: {
    id: number;
    name: string;
  };
  image?: string;
  notes?: string;
  created_at: string;
  branch: {
    id: number;
    name: string;
  };
}

export interface CustomerFormData {
  name: string;
  code?: string;
  phone: string;
  email?: string;
  address?: string;
  customer_type: 'individual' | 'company' | 'government';
  status: 'active' | 'inactive' | 'blocked';
  category_id?: number;
  image?: File;
  notes?: string;
  branch_id: number;
}

export interface CustomerFilters {
  search?: string;
  customer_type?: string;
  status?: string;
  category_id?: number;
  page?: number;
  page_size?: number;
}

export interface CustomerResponse {
  customers: Customer[];
  total: number;
  page: number;
  limit: number;
}