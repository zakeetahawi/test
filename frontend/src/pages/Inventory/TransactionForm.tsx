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
  Typography,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { Product } from '@/types/inventory';

interface TransactionFormData {
  type: 'in' | 'out';
  quantity: number;
  reference: string;
  notes?: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: TransactionFormData) => Promise<void>;
  product: Product;
}

const TransactionForm: React.FC<Props> = ({
  open,
  onClose,
  onSubmit,
  product,
}) => {
  const { t } = useTranslation();

  const validationSchema = Yup.object({
    type: Yup.string()
      .oneOf(['in', 'out'])
      .required(t('validation.required')),
    quantity: Yup.number()
      .min(0.1, t('validation.min_quantity'))
      .required(t('validation.required')),
    reference: Yup.string()
      .required(t('validation.required')),
  });

  const formik = useFormik<TransactionFormData>({
    initialValues: {
      type: 'in',
      quantity: 1,
      reference: '',
      notes: '',
    },
    validationSchema,
    onSubmit: async (values) => {
      await onSubmit(values);
      onClose();
    },
  });

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {t('inventory.add_transaction')}
      </DialogTitle>
      <form onSubmit={formik.handleSubmit}>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                {t('inventory.product')}: {product.name}
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                {t('inventory.current_stock')}: {product.stock} {product.unit}
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <FormControl 
                fullWidth 
                error={formik.touched.type && Boolean(formik.errors.type)}
              >
                <InputLabel>{t('inventory.transaction_type')}</InputLabel>
                <Select
                  name="type"
                  value={formik.values.type}
                  onChange={formik.handleChange}
                  label={t('inventory.transaction_type')}
                >
                  <MenuItem value="in">
                    {t('inventory.transaction_type.in')}
                  </MenuItem>
                  <MenuItem value="out">
                    {t('inventory.transaction_type.out')}
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="number"
                label={t('inventory.quantity')}
                name="quantity"
                value={formik.values.quantity}
                onChange={formik.handleChange}
                error={formik.touched.quantity && Boolean(formik.errors.quantity)}
                helperText={formik.touched.quantity && formik.errors.quantity}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      {product.unit}
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('inventory.reference')}
                name="reference"
                value={formik.values.reference}
                onChange={formik.handleChange}
                error={formik.touched.reference && Boolean(formik.errors.reference)}
                helperText={formik.touched.reference && formik.errors.reference}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label={t('inventory.notes')}
                name="notes"
                value={formik.values.notes}
                onChange={formik.handleChange}
              />
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
            {t('add')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default TransactionForm;