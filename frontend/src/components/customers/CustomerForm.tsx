import React from 'react';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import {
  Box,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Paper,
  Typography,
  Avatar
} from '@mui/material';
import { CustomerFormData, CustomerType } from '../../types/customer';
import { LoadingButton } from '@mui/lab';
import { Save as SaveIcon, ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface CustomerFormProps {
  initialValues?: CustomerType;
  onSubmit: (values: CustomerFormData) => Promise<void>;
  loading?: boolean;
}

const validationSchema = Yup.object({
  name: Yup.string().required('اسم العميل مطلوب'),
  phone: Yup.string()
    .required('رقم الهاتف مطلوب')
    .matches(/^[0-9+\s-]+$/, 'رقم هاتف غير صالح'),
  email: Yup.string()
    .email('بريد إلكتروني غير صالح')
    .nullable(),
  customer_type: Yup.string()
    .oneOf(['individual', 'company', 'government'], 'نوع عميل غير صالح')
    .required('نوع العميل مطلوب'),
  status: Yup.string()
    .oneOf(['active', 'inactive', 'blocked'], 'حالة غير صالحة')
    .required('الحالة مطلوبة'),
  branch_id: Yup.number()
    .required('الفرع مطلوب'),
});

export const CustomerForm: React.FC<CustomerFormProps> = ({
  initialValues,
  onSubmit,
  loading = false
}) => {
  const navigate = useNavigate();
  const [previewImage, setPreviewImage] = React.useState<string | undefined>(
    initialValues?.image
  );

  const formik = useFormik<CustomerFormData>({
    initialValues: {
      name: initialValues?.name || '',
      code: initialValues?.code,
      phone: initialValues?.phone || '',
      email: initialValues?.email || '',
      address: initialValues?.address || '',
      customer_type: initialValues?.customer_type || 'individual',
      status: initialValues?.status || 'active',
      category_id: initialValues?.category?.id,
      notes: initialValues?.notes || '',
      branch_id: initialValues?.branch.id || 0,
    },
    validationSchema,
    onSubmit: async (values) => {
      await onSubmit(values);
    },
  });

  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      formik.setFieldValue('image', file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h2">
          {initialValues ? 'تعديل بيانات العميل' : 'إضافة عميل جديد'}
        </Typography>
      </Box>

      <form onSubmit={formik.handleSubmit}>
        <Grid container spacing={3}>
          {/* صورة العميل */}
          <Grid item xs={12} display="flex" flexDirection="column" alignItems="center">
            <Avatar
              src={previewImage}
              sx={{ width: 100, height: 100, mb: 2 }}
            />
            <Button
              variant="outlined"
              component="label"
            >
              {initialValues ? 'تغيير الصورة' : 'إضافة صورة'}
              <input
                type="file"
                hidden
                accept="image/*"
                onChange={handleImageChange}
              />
            </Button>
          </Grid>

          {/* معلومات أساسية */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              name="name"
              label="اسم العميل"
              value={formik.values.name}
              onChange={formik.handleChange}
              error={formik.touched.name && Boolean(formik.errors.name)}
              helperText={formik.touched.name && formik.errors.name}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              name="phone"
              label="رقم الهاتف"
              value={formik.values.phone}
              onChange={formik.handleChange}
              error={formik.touched.phone && Boolean(formik.errors.phone)}
              helperText={formik.touched.phone && formik.errors.phone}
              inputProps={{ dir: 'ltr' }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              name="email"
              label="البريد الإلكتروني"
              type="email"
              value={formik.values.email}
              onChange={formik.handleChange}
              error={formik.touched.email && Boolean(formik.errors.email)}
              helperText={formik.touched.email && formik.errors.email}
              inputProps={{ dir: 'ltr' }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>نوع العميل</InputLabel>
              <Select
                name="customer_type"
                value={formik.values.customer_type}
                onChange={formik.handleChange}
                error={formik.touched.customer_type && Boolean(formik.errors.customer_type)}
                label="نوع العميل"
              >
                <MenuItem value="individual">فرد</MenuItem>
                <MenuItem value="company">شركة</MenuItem>
                <MenuItem value="government">حكومي</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              name="address"
              label="العنوان"
              multiline
              rows={3}
              value={formik.values.address}
              onChange={formik.handleChange}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>الحالة</InputLabel>
              <Select
                name="status"
                value={formik.values.status}
                onChange={formik.handleChange}
                error={formik.touched.status && Boolean(formik.errors.status)}
                label="الحالة"
              >
                <MenuItem value="active">نشط</MenuItem>
                <MenuItem value="inactive">غير نشط</MenuItem>
                <MenuItem value="blocked">محظور</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              name="notes"
              label="ملاحظات"
              multiline
              rows={4}
              value={formik.values.notes}
              onChange={formik.handleChange}
            />
          </Grid>

          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-start' }}>
              <Button
                variant="outlined"
                startIcon={<ArrowBackIcon />}
                onClick={() => navigate('/customers')}
              >
                إلغاء
              </Button>
              <LoadingButton
                type="submit"
                variant="contained"
                loading={loading}
                startIcon={<SaveIcon />}
              >
                {initialValues ? 'حفظ التغييرات' : 'إضافة العميل'}
              </LoadingButton>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};