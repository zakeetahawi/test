// filepath: d:\CRMsystem\frontend\src\pages\UserEdit.tsx
import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  Typography, 
  Box, 
  Paper,
  Breadcrumbs,
  Link,
  Alert,
  CircularProgress
} from '@mui/material';
import { NavigateNext as NavigateNextIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { UserUpdateRequest } from '../types/user';
import { useUser, useUpdateUser } from '../hooks/useUsers';
import UserForm from '../components/users/UserForm';

const UserEdit = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  
  // جلب بيانات المستخدم
  const { data: user, isLoading: isLoadingUser, error: userError } = useUser(id);
  
  // hook لتحديث المستخدم
  const updateUserMutation = useUpdateUser(id as string);

  const handleSubmit = async (userData: UserUpdateRequest) => {
    try {
      await updateUserMutation.mutateAsync(userData);
      enqueueSnackbar('تم تحديث بيانات المستخدم بنجاح', { variant: 'success' });
      navigate('/users');
    } catch (error: any) {
      enqueueSnackbar(
        `فشل في تحديث المستخدم: ${error?.response?.data?.detail || error.message || 'حدث خطأ ما'}`,
        { variant: 'error' }
      );
    }
  };

  // عرض مؤشر التحميل أثناء جلب بيانات المستخدم
  if (isLoadingUser) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // عرض رسالة خطأ في حالة وجود مشكلة في جلب بيانات المستخدم
  if (userError) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        خطأ في جلب بيانات المستخدم: {userError instanceof Error ? userError.message : 'حدث خطأ غير معروف'}
      </Alert>
    );
  }

  // إذا لم يتم العثور على المستخدم
  if (!user) {
    return (
      <Alert severity="warning" sx={{ mb: 3 }}>
        لم يتم العثور على المستخدم المطلوب
      </Alert>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* عنوان الصفحة ومسار التنقل */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4">
          تعديل بيانات المستخدم
        </Typography>
        <Breadcrumbs 
          separator={<NavigateNextIcon fontSize="small" />} 
          aria-label="مسار التنقل"
        >
          <Link color="inherit" href="/">الرئيسية</Link>
          <Link color="inherit" href="/users">إدارة المستخدمين</Link>
          <Typography color="textPrimary">تعديل المستخدم: {user.username}</Typography>
        </Breadcrumbs>
      </Box>

      {/* رسالة خطأ في حالة وجود خطأ */}
      {updateUserMutation.isError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {updateUserMutation.error instanceof Error 
            ? updateUserMutation.error.message 
            : 'حدث خطأ أثناء تحديث بيانات المستخدم'}
        </Alert>
      )}

      {/* نموذج تعديل بيانات المستخدم */}
      <Paper sx={{ p: 3 }}>
        <UserForm 
          user={user}
          onSubmit={handleSubmit} 
          isLoading={updateUserMutation.isLoading} 
        />
      </Paper>
    </Box>
  );
};

export default UserEdit;