import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { ProductFormData } from '@/types/inventory';

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: ProductFormData) => Promise<void>;
  initialData?: ProductFormData;
  isEdit?: boolean;
  categories: { id: string; name: string }[];
}

const ProductForm: React.FC<Props> = ({
  open,
  onClose,
  onSubmit,
  initialData,
  isEdit = false,
  categories,
}) => {
  const { t } = useTranslation();

  const validationSchema = Yup.object({
    code: Yup.string().required(t('validation.required')),
    name: Yup.string().required(t('validation.required')),
    category: Yup.string().required(t('validation.required')),
    unit: Yup.string().required(t('validation.required')),
    price: Yup.number()
      .min(0, t('validation.min_zero'))
      .required(t('validation.required')),
    stock: Yup.number()
      .min(0, t('validation.min_zero'))
      .required(t('validation.required')),
    minStock: Yup.number()
      .min(0, t('validation.min_zero'))
      .required(t('validation.required')),
    maxStock: Yup.number()
      .min(0, t('validation.min_zero'))
      .required(t('validation.required')),
    status: Yup.string()
      .oneOf(['active', 'inactive'])
      .required(t('validation.required')),
  });

  const formik = useFormik({
    initialValues: initialData || {
      code: '',
      name: '',
      description: '',
      category: '',
      unit: '',
      price: 0,
      stock: 0,
      minStock: 0,
      maxStock: 0,
      status: 'active',
    },
    validationSchema,
    onSubmit: async (values) => {
      await onSubmit(values);
      onClose();
    },
  });

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {isEdit ? t('inventory.edit_product') : t('inventory.add_product')}
      </DialogTitle>
      <form onSubmit={formik.handleSubmit}>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('inventory.code')}
                name="code"
                value={formik.values.code}
                onChange={formik.handleChange}
                error={formik.touched.code && Boolean(formik.errors.code)}
                helperText={formik.touched.code && formik.errors.code}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('inventory.name')}
                name="name"
                value={formik.values.name}
                onChange={formik.handleChange}
                error={formik.touched.name && Boolean(formik.errors.name)}
                helperText={formik.touched.name && formik.errors.name}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label={t('inventory.description')}
                name="description"
                value={formik.values.description}
                onChange={formik.handleChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl 
                fullWidth 
                error={formik.touched.category && Boolean(formik.errors.category)}
              >
                <InputLabel>{t('inventory.category')}</InputLabel>
                <Select
                  name="category"
                  value={formik.values.category}
                  onChange={formik.handleChange}
                  label={t('inventory.category')}
                >
                  {categories.map((category) => (
                    <MenuItem key={category.id} value={category.id}>
                      {category.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('inventory.unit')}
                name="unit"
                value={formik.values.unit}
                onChange={formik.handleChange}
                error={formik.touched.unit && Boolean(formik.errors.unit)}
                helperText={formik.touched.unit && formik.errors.unit}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label={t('inventory.price')}
                name="price"
                value={formik.values.price}
                onChange={formik.handleChange}
                error={formik.touched.price && Boolean(formik.errors.price)}
                helperText={formik.touched.price && formik.errors.price}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">₪</InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label={t('inventory.stock')}
                name="stock"
                value={formik.values.stock}
                onChange={formik.handleChange}
                error={formik.touched.stock && Boolean(formik.errors.stock)}
                helperText={formik.touched.stock && formik.errors.stock}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      {formik.values.unit}
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label={t('inventory.min_stock')}
                name="minStock"
                value={formik.values.minStock}
                onChange={formik.handleChange}
                error={formik.touched.minStock && Boolean(formik.errors.minStock)}
                helperText={formik.touched.minStock && formik.errors.minStock}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      {formik.values.unit}
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label={t('inventory.max_stock')}
                name="maxStock"
                value={formik.values.maxStock}
                onChange={formik.handleChange}
                error={formik.touched.maxStock && Boolean(formik.errors.maxStock)}
                helperText={formik.touched.maxStock && formik.errors.maxStock}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      {formik.values.unit}
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl 
                fullWidth 
                error={formik.touched.status && Boolean(formik.errors.status)}
              >
                <InputLabel>{t('inventory.status')}</InputLabel>
                <Select
                  name="status"
                  value={formik.values.status}
                  onChange={formik.handleChange}
                  label={t('inventory.status')}
                >
                  <MenuItem value="active">
                    {t('inventory.status.active')}
                  </MenuItem>
                  <MenuItem value="inactive">
                    {t('inventory.status.inactive')}
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} color="inherit">
            {t('cancel')}
          </Button>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={formik.isSubmitting}
          >
            {isEdit ? t('save') : t('add')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default ProductForm;