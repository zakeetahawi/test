// filepath: d:\CRMsystem\frontend\src\components\users\UserForm.tsx
import React from 'react';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import {
  Box,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Switch,
  FormControlLabel,
  CircularProgress,
  Typography,
} from '@mui/material';
import { useRoles } from '../../hooks/useUsers';
import { User, UserCreateRequest, UserUpdateRequest } from '../../types/user';

interface UserFormProps {
  user?: User;
  onSubmit: (values: UserCreateRequest | UserUpdateRequest) => void;
  isLoading: boolean;
}

const UserForm: React.FC<UserFormProps> = ({ user, onSubmit, isLoading }) => {
  const { data: roles, isLoading: rolesLoading } = useRoles();
  const isEditMode = !!user;

  // إنشاء مخطط التحقق باستخدام Yup
  const validationSchema = Yup.object({
    username: isEditMode 
      ? Yup.string()
      : Yup.string()
          .required('اسم المستخدم مطلوب')
          .min(3, 'اسم المستخدم يجب أن يكون على الأقل 3 أحرف')
          .matches(/^[a-zA-Z0-9_]+$/, 'اسم المستخدم يجب أن يحتوي على أحرف إنجليزية وأرقام فقط'),
    email: Yup.string()
      .email('البريد الإلكتروني غير صالح')
      .required('البريد الإلكتروني مطلوب'),
    first_name: Yup.string()
      .required('الاسم الأول مطلوب'),
    last_name: Yup.string()
      .required('الاسم الأخير مطلوب'),
    password: isEditMode
      ? Yup.string()
      : Yup.string()
          .required('كلمة المرور مطلوبة')
          .min(8, 'كلمة المرور يجب أن تكون على الأقل 8 أحرف'),
    confirm_password: isEditMode 
      ? Yup.string()
          .oneOf([Yup.ref('password')], 'كلمة المرور غير متطابقة')
      : Yup.string()
          .required('تأكيد كلمة المرور مطلوب')
          .oneOf([Yup.ref('password')], 'كلمة المرور غير متطابقة'),
    role_id: Yup.number()
      .required('الدور مطلوب'),
    phone: Yup.string()
      .matches(/^[0-9+\s]+$/, 'رقم الهاتف يجب أن يحتوي على أرقام فقط'),
    department: Yup.string(),
  });

  // إعداد الفورم باستخدام Formik
  const formik = useFormik({
    initialValues: {
      username: user?.username || '',
      email: user?.email || '',
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      password: '',
      confirm_password: '',
      role_id: user?.role.id || 0,
      is_active: user?.is_active ?? true,
      phone: user?.phone || '',
      department: user?.department || '',
    },
    validationSchema,
    onSubmit: (values) => {
      // تنسيق البيانات وإرسالها
      const userData: UserCreateRequest | UserUpdateRequest = {
        ...values,
      };

      // في حالة التعديل، نحذف الحقول الفارغة غير المطلوبة
      if (isEditMode) {
        if (!values.password) {
          delete userData.password;
        }
        // لا نرسل اسم المستخدم عند التعديل
        delete (userData as any).username;
        delete (userData as any).confirm_password;
      }

      onSubmit(userData);
    },
  });

  return (
    <form onSubmit={formik.handleSubmit}>
      <Grid container spacing={3}>
        {/* معلومات الحساب */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            معلومات الحساب
          </Typography>
        </Grid>

        {!isEditMode && (
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              id="username"
              name="username"
              label="اسم المستخدم"
              value={formik.values.username}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.username && Boolean(formik.errors.username)}
              helperText={formik.touched.username && formik.errors.username}
              disabled={isLoading}
            />
          </Grid>
        )}

        <Grid item xs={12} md={isEditMode ? 12 : 6}>
          <TextField
            fullWidth
            id="email"
            name="email"
            label="البريد الإلكتروني"
            type="email"
            value={formik.values.email}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.email && Boolean(formik.errors.email)}
            helperText={formik.touched.email && formik.errors.email}
            disabled={isLoading}
          />
        </Grid>

        {/* كلمة المرور */}
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="password"
            name="password"
            label={isEditMode ? "كلمة المرور الجديدة (اتركها فارغة للإبقاء على الحالية)" : "كلمة المرور"}
            type="password"
            value={formik.values.password}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.password && Boolean(formik.errors.password)}
            helperText={formik.touched.password && formik.errors.password}
            disabled={isLoading}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="confirm_password"
            name="confirm_password"
            label="تأكيد كلمة المرور"
            type="password"
            value={formik.values.confirm_password}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.confirm_password && Boolean(formik.errors.confirm_password)}
            helperText={formik.touched.confirm_password && formik.errors.confirm_password}
            disabled={isLoading || (!isEditMode && !formik.values.password)}
          />
        </Grid>

        {/* معلومات شخصية */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            المعلومات الشخصية
          </Typography>
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="first_name"
            name="first_name"
            label="الاسم الأول"
            value={formik.values.first_name}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.first_name && Boolean(formik.errors.first_name)}
            helperText={formik.touched.first_name && formik.errors.first_name}
            disabled={isLoading}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="last_name"
            name="last_name"
            label="الاسم الأخير"
            value={formik.values.last_name}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.last_name && Boolean(formik.errors.last_name)}
            helperText={formik.touched.last_name && formik.errors.last_name}
            disabled={isLoading}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="phone"
            name="phone"
            label="رقم الهاتف"
            value={formik.values.phone}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.phone && Boolean(formik.errors.phone)}
            helperText={formik.touched.phone && formik.errors.phone}
            disabled={isLoading}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="department"
            name="department"
            label="القسم"
            value={formik.values.department}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.department && Boolean(formik.errors.department)}
            helperText={formik.touched.department && formik.errors.department}
            disabled={isLoading}
          />
        </Grid>

        {/* إعدادات الحساب */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            إعدادات الحساب
          </Typography>
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl 
            fullWidth 
            error={formik.touched.role_id && Boolean(formik.errors.role_id)}
            disabled={isLoading || rolesLoading}
          >
            <InputLabel id="role-label">الدور</InputLabel>
            <Select
              labelId="role-label"
              id="role_id"
              name="role_id"
              value={formik.values.role_id || ''}
              label="الدور"
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
            >
              {rolesLoading ? (
                <MenuItem value={0} disabled>جاري التحميل...</MenuItem>
              ) : roles ? (
                roles.map((role) => (
                  <MenuItem key={role.id} value={role.id}>
                    {role.name}
                  </MenuItem>
                ))
              ) : (
                <MenuItem value={0} disabled>لا توجد أدوار متاحة</MenuItem>
              )}
            </Select>
            {formik.touched.role_id && formik.errors.role_id && (
              <FormHelperText>{formik.errors.role_id as string}</FormHelperText>
            )}
          </FormControl>
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Switch
                id="is_active"
                name="is_active"
                checked={formik.values.is_active}
                onChange={formik.handleChange}
                disabled={isLoading}
              />
            }
            label="حساب نشط"
          />
        </Grid>

        {/* أزرار التحكم */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={isLoading || rolesLoading}
              sx={{ minWidth: 120 }}
            >
              {isLoading ? (
                <CircularProgress size={24} />
              ) : isEditMode ? (
                'حفظ التغييرات'
              ) : (
                'إضافة مستخدم'
              )}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </form>
  );
};

export default UserForm;