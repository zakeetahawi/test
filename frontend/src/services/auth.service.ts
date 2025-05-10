import { api } from './api';
import { useMutation, useQueryClient } from 'react-query';
import { AxiosError } from 'axios';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    try {
      const { data } = await api.post('/api/token/', credentials);
      if (data.access) {
        const userData = { access: data.access, refresh: data.refresh };
        localStorage.setItem('user', JSON.stringify(userData));
        api.defaults.headers.Authorization = `Bearer ${data.access}`;
      }
      return data;
    } catch (error) {
      if (error instanceof AxiosError) {
        console.error('Login error:', error.response?.data);
      }
      throw error;
    }
  },

  async refreshToken(refresh: string): Promise<AuthTokens> {
    const response = await api.post('/api/token/refresh/', { refresh });
    return response.data;
  },

  logout(): void {
    localStorage.removeItem('user');
    delete api.defaults.headers.Authorization;
  },

  getCurrentUser(): AuthTokens | null {
    const userStr = localStorage.getItem('user');
    if (userStr) return JSON.parse(userStr);
    return null;
  }
};

export const useLoginMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation<AuthTokens, AxiosError, LoginCredentials>(
    async (credentials) => authService.login(credentials),
    {
      onSuccess: (data) => {
        queryClient.setQueryData('user', data);
      },
      onError: (error: AxiosError) => {
        console.error('Login failed:', error.response?.data);
        throw error;
      },
    }
  );
};