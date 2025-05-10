// filepath: d:\CRMsystem\frontend\src\types\user.ts
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  role: {
    id: number;
    name: string;
  };
  is_active: boolean;
  date_joined: string;
  last_login?: string;
  permissions: string[];
  phone?: string;
  department?: string;
  profile_image?: string;
}

export interface UserCreateRequest {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password?: string;
  role_id: number;
  is_active?: boolean;
  phone?: string;
  department?: string;
}

export interface UserUpdateRequest {
  email?: string;
  first_name?: string;
  last_name?: string;
  role_id?: number;
  is_active?: boolean;
  phone?: string;
  department?: string;
}

export interface Role {
  id: number;
  name: string;
  permissions: Permission[];
}

export interface Permission {
  id: number;
  name: string;
  codename: string;
}