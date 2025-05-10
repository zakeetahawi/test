import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { authService } from '../authService';

vi.mock('axios');

describe('authService', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('login', () => {
    const mockCredentials = { username: 'testuser', password: 'password123' };
    const mockResponse = { access: 'access-token', refresh: 'refresh-token' };

    it('should store tokens in localStorage on successful login', async () => {
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockResponse });
      
      await authService.login(mockCredentials);
      
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockResponse));
    });

    it('should return tokens on successful login', async () => {
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockResponse });
      
      const result = await authService.login(mockCredentials);
      
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getCurrentUser', () => {
    it('should return null when no user in localStorage', () => {
      expect(authService.getCurrentUser()).toBeNull();
    });

    it('should return user data when available in localStorage', () => {
      const mockUser = { access: 'token', refresh: 'refresh' };
      localStorage.setItem('user', JSON.stringify(mockUser));
      
      expect(authService.getCurrentUser()).toEqual(mockUser);
    });
  });
});