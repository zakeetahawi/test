import axiosInstance from './axios';
import { AxiosResponse } from 'axios';

export class ApiService {
    private static handleResponse<T>(response: AxiosResponse<T>): T {
        return response.data;
    }

    static async get<T>(url: string, params?: any): Promise<T> {
        const response = await axiosInstance.get<T>(url, { params });
        return this.handleResponse(response);
    }

    static async post<T>(url: string, data?: any): Promise<T> {
        const response = await axiosInstance.post<T>(url, data);
        return this.handleResponse(response);
    }

    static async put<T>(url: string, data: any): Promise<T> {
        const response = await axiosInstance.put<T>(url, data);
        return this.handleResponse(response);
    }

    static async delete<T>(url: string): Promise<T> {
        const response = await axiosInstance.delete<T>(url);
        return this.handleResponse(response);
    }

    static async patch<T>(url: string, data: any): Promise<T> {
        const response = await axiosInstance.patch<T>(url, data);
        return this.handleResponse(response);
    }
}