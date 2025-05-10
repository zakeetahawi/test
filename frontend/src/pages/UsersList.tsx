// filepath: d:\CRMsystem\frontend\src\pages\UsersList.tsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Chip,
  Button,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  CircularProgress,
  Alert,
  Grid,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  LockReset as ResetPasswordIcon,
} from '@mui/icons-material';
import { useUsers, useRoles, useDeleteUser, useToggleUserStatus, useResetPassword } from '../hooks/useUsers';
import { useSnackbar } from 'notistack';
import { formatDate } from '../utils/formatDate';
import { User } from '../types/user';

const UsersList = () => {
  // حالة البحث والتصفية
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false);
  const [tempPassword, setTempPassword] = useState<string | null>(null);

  // استخدام hooks
  const { enqueueSnackbar } = useSnackbar();
  const { data, isLoading, error, refetch } = useUsers({
    page: page + 1,
    size: rowsPerPage,
    search: searchTerm,
    role: roleFilter,
    isActive: statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined,
  });
  const { data: roles } = useRoles();
  const deleteUserMutation = useDeleteUser();
  const toggleStatusMutation = useToggleUserStatus();
  const resetPasswordMutation = useResetPassword();

  // التعامل مع تغيير الصفحة
  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  // التعامل مع تغيير عدد الصفوف في الصفحة
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // التعامل مع تغيير مصطلح البحث
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };

  // فتح نافذة تأكيد الحذف
  const handleDeleteClick = (userId: number) => {
    setSelectedUserId(userId);
    setDeleteDialogOpen(true);
  };

  // تنفيذ عملية الحذف
  const confirmDelete = async () => {
    if (selectedUserId) {
      try {
        await deleteUserMutation.mutateAsync(selectedUserId);
        enqueueSnackbar('تم حذف المستخدم بنجاح', { variant: 'success' });
      } catch (error) {
        enqueueSnackbar('فشل في حذف المستخدم', { variant: 'error' });
      }
      setDeleteDialogOpen(false);
    }
  };

  // تغيير حالة المستخدم (نشط/غير نشط)
  const handleToggleStatus = async (user: User) => {
    try {
      await toggleStatusMutation.mutateAsync({
        id: user.id,
        isActive: !user.is_active,
      });
      enqueueSnackbar(
        `تم ${user.is_active ? 'تعطيل' : 'تفعيل'} المستخدم بنجاح`, 
        { variant: 'success' }
      );
    } catch (error) {
      enqueueSnackbar('فشل في تغيير حالة المستخدم', { variant: 'error' });
    }
  };

  // فتح نافذة إعادة تعيين كلمة المرور
  const handleResetPasswordClick = (userId: number) => {
    setSelectedUserId(userId);
    setResetPasswordDialogOpen(true);
    setTempPassword(null);
  };

  // تنفيذ إعادة تعيين كلمة المرور
  const confirmResetPassword = async () => {
    if (selectedUserId) {
      try {
        const result = await resetPasswordMutation.mutateAsync({
          id: selectedUserId,
          generateTemp: true
        });
        setTempPassword(result.temp_password || null);
        enqueueSnackbar('تم إعادة تعيين كلمة المرور بنجاح', { variant: 'success' });
      } catch (error) {
        enqueueSnackbar('فشل في إعادة تعيين كلمة المرور', { variant: 'error' });
        setResetPasswordDialogOpen(false);
      }
    }
  };

  // محتوى الصفحة الرئيسي
  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4">
          إدارة المستخدمين
        </Typography>
        <Button
          component={Link}
          to="/users/add"
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
        >
          إضافة مستخدم
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          حدث خطأ أثناء تحميل بيانات المستخدمين: {error instanceof Error ? error.message : 'خطأ غير معروف'}
        </Alert>
      )}

      {/* قسم البحث والتصفية */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="بحث"
              value={searchTerm}
              onChange={handleSearchChange}
              variant="outlined"
              placeholder="البحث بالاسم، البريد الإلكتروني، أو اسم المستخدم..."
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel id="role-filter-label">الدور</InputLabel>
              <Select
                labelId="role-filter-label"
                value={roleFilter}
                onChange={(e) => {
                  setRoleFilter(e.target.value);
                  setPage(0);
                }}
                label="الدور"
              >
                <MenuItem value="">الكل</MenuItem>
                {roles?.map((role) => (
                  <MenuItem key={role.id} value={role.id.toString()}>{role.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel id="status-filter-label">الحالة</InputLabel>
              <Select
                labelId="status-filter-label"
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(0);
                }}
                label="الحالة"
              >
                <MenuItem value="">الكل</MenuItem>
                <MenuItem value="active">نشط</MenuItem>
                <MenuItem value="inactive">غير نشط</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => refetch()}
            >
              تحديث
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* جدول المستخدمين */}
      <Paper>
        <TableContainer>
          <Table aria-label="جدول المستخدمين">
            <TableHead>
              <TableRow>
                <TableCell>المستخدم</TableCell>
                <TableCell>البريد الإلكتروني</TableCell>
                <TableCell>الدور</TableCell>
                <TableCell>تاريخ الإنضمام</TableCell>
                <TableCell>آخر تسجيل دخول</TableCell>
                <TableCell>الحالة</TableCell>
                <TableCell align="center">الإجراءات</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                      <CircularProgress />
                    </Box>
                  </TableCell>
                </TableRow>
              ) : data?.users && data.users.length > 0 ? (
                data.users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {user.full_name || `${user.first_name} ${user.last_name}`}
                        <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                          ({user.username})
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={user.role.name}
                        size="small"
                        color={
                          user.role.name === 'مدير' ? 'primary' :
                          user.role.name === 'مشرف' ? 'secondary' : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell>{formatDate(user.date_joined)}</TableCell>
                    <TableCell>{user.last_login ? formatDate(user.last_login) : 'لم يسجل الدخول بعد'}</TableCell>
                    <TableCell>
                      <Chip
                        label={user.is_active ? 'نشط' : 'غير نشط'}
                        size="small"
                        color={user.is_active ? 'success' : 'error'}
                        onClick={() => handleToggleStatus(user)}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        component={Link}
                        to={`/users/edit/${user.id}`}
                        color="primary"
                        size="small"
                        aria-label="تعديل"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        color="error"
                        size="small"
                        aria-label="حذف"
                        onClick={() => handleDeleteClick(user.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        color="warning"
                        size="small"
                        aria-label="إعادة تعيين كلمة المرور"
                        onClick={() => handleResetPasswordClick(user.id)}
                      >
                        <ResetPasswordIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    لا توجد بيانات للعرض
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={data?.total || 0}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="عدد الصفوف في الصفحة:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} من ${count}`}
        />
      </Paper>

      {/* نافذة تأكيد الحذف */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title">
          تأكيد الحذف
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            هل أنت متأكد من رغبتك في حذف هذا المستخدم؟ لا يمكن التراجع عن هذا الإجراء.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>إلغاء</Button>
          <Button
            onClick={confirmDelete}
            color="error"
            autoFocus
            disabled={deleteUserMutation.isLoading}
          >
            {deleteUserMutation.isLoading ? <CircularProgress size={24} /> : 'حذف'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* نافذة إعادة تعيين كلمة المرور */}
      <Dialog
        open={resetPasswordDialogOpen}
        onClose={() => {
          if (!resetPasswordMutation.isLoading) {
            setResetPasswordDialogOpen(false);
          }
        }}
        aria-labelledby="reset-password-dialog-title"
      >
        <DialogTitle id="reset-password-dialog-title">
          إعادة تعيين كلمة المرور
        </DialogTitle>
        <DialogContent>
          {!tempPassword ? (
            <DialogContentText>
              هل ترغب في إعادة تعيين كلمة المرور لهذا المستخدم وإنشاء كلمة مرور مؤقتة؟
            </DialogContentText>
          ) : (
            <Box>
              <DialogContentText>
                تم إعادة تعيين كلمة المرور بنجاح. الرجاء حفظ كلمة المرور المؤقتة التالية:
              </DialogContentText>
              <Box sx={{ 
                bgcolor: 'background.paper', 
                p: 2, 
                my: 2, 
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
                textAlign: 'center'
              }}>
                <Typography variant="h6" component="div">
                  {tempPassword}
                </Typography>
              </Box>
              <DialogContentText color="error">
                ملاحظة: لن تتمكن من رؤية كلمة المرور هذه مرة أخرى بعد إغلاق هذه النافذة.
              </DialogContentText>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetPasswordDialogOpen(false)}>
            {tempPassword ? 'إغلاق' : 'إلغاء'}
          </Button>
          {!tempPassword && (
            <Button
              onClick={confirmResetPassword}
              color="warning"
              autoFocus
              disabled={resetPasswordMutation.isLoading}
            >
              {resetPasswordMutation.isLoading ? (
                <CircularProgress size={24} />
              ) : (
                'إعادة تعيين'
              )}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UsersList;