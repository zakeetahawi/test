import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useQuery } from 'react-query';
import { Product } from '@/types/inventory';
import inventoryService from '@/services/inventoryService';

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: Omit<Product, 'id'>) => void;
  initialData?: Product;
  isEdit?: boolean;
}

const ProductForm: React.FC<Props> = ({
  open,
  onClose,
  onSubmit,
  initialData,
  isEdit = false,
}) => {
  const { t } = useTranslation();
  const { control, handleSubmit, formState: { errors } } = useForm({
    defaultValues: initialData || {
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
  });

  const { data: categories = [] } = useQuery(
    'categories',
    inventoryService.getCategories
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {isEdit ? t('inventory.edit_product') : t('inventory.add_product')}
      </DialogTitle>
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="code"
                control={control}
                rules={{ required: true }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label={t('inventory.code')}
                    fullWidth
                    error={!!errors.code}
                    helperText={errors.code ? t('form.required') : ''}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Controller
                name="name"
                control={control}
                rules={{ required: true }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label={t('inventory.name')}
                    fullWidth
                    error={!!errors.name}
                    helperText={errors.name ? t('form.required') : ''}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Controller
                name="description"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label={t('inventory.description')}
                    fullWidth
                    multiline
                    rows={3}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Controller
                name="category"
                control={control}
                rules={{ required: true }}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.category}>
                    <InputLabel>{t('inventory.category')}</InputLabel>
                    <Select {...field} label={t('inventory.category')}>
                      {categories.map((category: any) => (
                        <MenuItem key={category.id} value={category.name}>
                          {category.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Controller
                name="unit"
                control={control}
                rules={{ required: true }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label={t('inventory.unit')}
                    fullWidth
                    error={!!errors.unit}
                    helperText={errors.unit ? t('form.required') : ''}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Controller
                name="price"
                control={control}
                rules={{ required: true, min: 0 }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label={t('inventory.price')}
                    fullWidth
                    error={!!errors.price}
                    helperText={errors.price ? t('form.invalid_price') : ''}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">₪</InputAdornment>
                      ),
                    }}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Controller
                name="stock"
                control={control}
                rules={{ required: true, min: 0 }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label={t('inventory.stock')}
                    fullWidth
                    error={!!errors.stock}
                    helperText={errors.stock ? t('form.invalid_stock') : ''}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Controller
                name="minStock"
                control={control}
                rules={{ required: true, min: 0 }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label={t('inventory.min_stock')}
                    fullWidth
                    error={!!errors.minStock}
                    helperText={errors.minStock ? t('form.invalid_min_stock') : ''}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Controller
                name="maxStock"
                control={control}
                rules={{ required: true, min: 0 }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label={t('inventory.max_stock')}
                    fullWidth
                    error={!!errors.maxStock}
                    helperText={errors.maxStock ? t('form.invalid_max_stock') : ''}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Controller
                name="status"
                control={control}
                rules={{ required: true }}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>{t('inventory.status')}</InputLabel>
                    <Select {...field} label={t('inventory.status')}>
                      <MenuItem value="active">
                        {t('inventory.status.active')}
                      </MenuItem>
                      <MenuItem value="inactive">
                        {t('inventory.status.inactive')}
                      </MenuItem>
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>
          </Grid>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={onClose}>
            {t('cancel')}
          </Button>
          <Button type="submit" variant="contained" color="primary">
            {isEdit ? t('save') : t('add')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default ProductForm;