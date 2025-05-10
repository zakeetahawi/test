// filepath: d:\CRMsystem\frontend\src\pages\UserAdd.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Typography, 
  Box, 
  Paper,
  Breadcrumbs,
  Link,
  Alert
} from '@mui/material';
import { NavigateNext as NavigateNextIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { UserCreateRequest } from '../types/user';
import { useCreateUser } from '../hooks/useUsers';
import UserForm from '../components/users/UserForm';

const UserAdd = () => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const createUserMutation = useCreateUser();

  const handleSubmit = async (userData: UserCreateRequest) => {
    try {
      await createUserMutation.mutateAsync(userData);
      enqueueSnackbar('تم إضافة المستخدم بنجاح', { variant: 'success' });
      navigate('/users');
    } catch (error: any) {
      enqueueSnackbar(
        `فشل في إضافة المستخدم: ${error?.response?.data?.detail || error.message || 'حدث خطأ ما'}`,
        { variant: 'error' }
      );
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* عنوان الصفحة ومسار التنقل */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4">
          إضافة مستخدم جديد
        </Typography>
        <Breadcrumbs 
          separator={<NavigateNextIcon fontSize="small" />} 
          aria-label="مسار التنقل"
        >
          <Link color="inherit" href="/">الرئيسية</Link>
          <Link color="inherit" href="/users">إدارة المستخدمين</Link>
          <Typography color="textPrimary">إضافة مستخدم</Typography>
        </Breadcrumbs>
      </Box>

      {/* رسالة خطأ في حالة وجود خطأ */}
      {createUserMutation.isError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {createUserMutation.error instanceof Error 
            ? createUserMutation.error.message 
            : 'حدث خطأ أثناء إضافة المستخدم'}
        </Alert>
      )}

      {/* نموذج إضافة المستخدم */}
      <Paper sx={{ p: 3 }}>
        <UserForm 
          onSubmit={handleSubmit} 
          isLoading={createUserMutation.isLoading} 
        />
      </Paper>
    </Box>
  );
};

export default UserAdd;