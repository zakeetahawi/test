// filepath: d:\CRMsystem\frontend\src\hooks\useUsers.ts
import { useQuery, useMutation, useQueryClient } from 'react-query';
import userService, { UserListParams } from '../services/userService';
import { User, UserCreateRequest, UserUpdateRequest } from '../types/user';

export const useUsers = (params: UserListParams = {}) => {
  return useQuery(['users', params], () => userService.getUsers(params), {
    keepPreviousData: true,
  });
};

export const useUser = (id: number | string | undefined) => {
  return useQuery(['user', id], () => id ? userService.getUser(id) : Promise.reject('No user ID provided'), {
    enabled: !!id,
  });
};

export const useRoles = () => {
  return useQuery('roles', userService.getRoles);
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation((userData: UserCreateRequest) => userService.createUser(userData), {
    onSuccess: () => {
      queryClient.invalidateQueries('users');
    },
  });
};

export const useUpdateUser = (id: number | string) => {
  const queryClient = useQueryClient();
  return useMutation((userData: UserUpdateRequest) => userService.updateUser(id, userData), {
    onSuccess: (updatedUser) => {
      queryClient.invalidateQueries(['users']);
      queryClient.invalidateQueries(['user', id]);
      queryClient.setQueryData(['user', id], updatedUser);
    },
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  return useMutation(
    (id: number | string) => userService.deleteUser(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('users');
      },
    }
  );
};

export const useToggleUserStatus = () => {
  const queryClient = useQueryClient();
  return useMutation(
    ({ id, isActive }: { id: number | string; isActive: boolean }) => 
      userService.toggleUserStatus(id, isActive),
    {
      onSuccess: (updatedUser: User) => {
        queryClient.invalidateQueries('users');
        queryClient.invalidateQueries(['user', updatedUser.id]);
        queryClient.setQueryData(['user', updatedUser.id], updatedUser);
      },
    }
  );
};

export const useResetPassword = () => {
  return useMutation(
    ({ id, generateTemp }: { id: number | string; generateTemp?: boolean }) => 
      userService.resetPassword(id, generateTemp)
  );
};