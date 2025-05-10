export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
}

export interface UserData {
  id: number;
  username: string;
  email: string;
  fullName: string;
  role: string;
  permissions: string[];
  isActive: boolean;
  lastLogin: string;
}

export interface AuthState {
  user: UserData | null;
  isLoading: boolean;
  error: string | null;
}

export interface TokenPayload {
  exp: number;
  iat: number;
  jti: string;
  token_type: string;
  user_id: number;
}