import { ApiService } from './api.service';
import { AxiosResponse } from 'axios';

export interface CustomerFilters {
    page?: number;
    page_size?: number;
    search?: string;
    status?: 'active' | 'inactive';
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
}

export interface Customer {
    id: number;
    name: string;
    email: string;
    phone: string;
    address: string;
    status: 'active' | 'inactive';
    created_at: string;
    updated_at: string;
    notes?: string;
}

export interface CustomerFormData {
    name: string;
    email: string;
    phone: string;
    address: string;
    status?: 'active' | 'inactive';
    notes?: string;
}

export interface CustomerListResponse {
    count: number;
    next: string | null;
    previous: string | null;
    results: Customer[];
}

export class CustomerService {
    private static readonly BASE_URL = '/api/customers';

    static async getCustomers(filters: CustomerFilters = {}): Promise<CustomerListResponse> {
        return ApiService.get(this.BASE_URL, filters);
    }

    static async getCustomer(id: number): Promise<Customer> {
        return ApiService.get(`${this.BASE_URL}/${id}`);
    }

    static async createCustomer(data: CustomerFormData): Promise<Customer> {
        return ApiService.post(this.BASE_URL, data);
    }

    static async updateCustomer(id: number, data: Partial<CustomerFormData>): Promise<Customer> {
        return ApiService.patch(`${this.BASE_URL}/${id}`, data);
    }

    static async deleteCustomer(id: number): Promise<void> {
        return ApiService.delete(`${this.BASE_URL}/${id}`);
    }

    static async searchCustomers(query: string): Promise<Customer[]> {
        return ApiService.get(`${this.BASE_URL}/search`, { query });
    }

    static async exportCustomers(filters: CustomerFilters): Promise<Blob> {
        const response: AxiosResponse<Blob> = await ApiService.get(
            `${this.BASE_URL}/export`,
            {
                ...filters,
                responseType: 'blob'
            }
        );
        return response.data;
    }

    static async importCustomers(file: File): Promise<void> {
        const formData = new FormData();
        formData.append('file', file);
        return ApiService.post(`${this.BASE_URL}/import`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
    }

    static async bulkUpdateStatus(
        customerIds: number[],
        status: 'active' | 'inactive'
    ): Promise<void> {
        return ApiService.post(`${this.BASE_URL}/bulk-update-status`, {
            customer_ids: customerIds,
            status
        });
    }
}