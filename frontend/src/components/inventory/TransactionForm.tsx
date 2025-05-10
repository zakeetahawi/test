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
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Product } from '@/types/inventory';

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: {
    productId: number;
    type: 'in' | 'out';
    quantity: number;
    reference: string;
    notes?: string;
  }) => void;
  product?: Product;
}

const TransactionForm: React.FC<Props> = ({
  open,
  onClose,
  onSubmit,
  product,
}) => {
  const { t } = useTranslation();
  const { control, handleSubmit, formState: { errors }, watch } = useForm({
    defaultValues: {
      type: 'in',
      quantity: 1,
      reference: '',
      notes: '',
    },
  });

  const transactionType = watch('type');

  const validateQuantity = (value: number) => {
    if (value <= 0) return 'form.invalid_quantity';
    if (transactionType === 'out' && product && value > product.stock) {
      return 'inventory.error.insufficient_stock';
    }
    return true;
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {t('inventory.add_transaction')}
      </DialogTitle>
      
      <form onSubmit={handleSubmit((data) => onSubmit({ ...data, productId: product?.id || 0 }))}>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Controller
                name="type"
                control={control}
                rules={{ required: true }}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>{t('inventory.transaction_type')}</InputLabel>
                    <Select {...field} label={t('inventory.transaction_type')}>
                      <MenuItem value="in">
                        {t('inventory.transaction_type.in')}
                      </MenuItem>
                      <MenuItem value="out">
                        {t('inventory.transaction_type.out')}
                      </MenuItem>
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Controller
                name="quantity"
                control={control}
                rules={{
                  required: true,
                  validate: validateQuantity,
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label={t('inventory.quantity')}
                    fullWidth
                    error={!!errors.quantity}
                    helperText={
                      errors.quantity
                        ? t(errors.quantity.message as string)
                        : ''
                    }
                    InputProps={{
                      endAdornment: product?.unit,
                    }}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Controller
                name="reference"
                control={control}
                rules={{ required: true }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label={t('inventory.reference')}
                    fullWidth
                    error={!!errors.reference}
                    helperText={errors.reference ? t('form.required') : ''}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Controller
                name="notes"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label={t('inventory.notes')}
                    fullWidth
                    multiline
                    rows={3}
                  />
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
            {t('add')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default TransactionForm;