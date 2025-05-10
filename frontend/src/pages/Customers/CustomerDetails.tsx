import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  Typography,
  Chip,
  Box,
  Divider,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { Customer } from '@/types/customer';

interface Props {
  customer: Customer;
  open: boolean;
  onClose: () => void;
  onEdit: () => void;
}

const InfoRow: React.FC<{ label: string; value: string | React.ReactNode }> = ({ label, value }) => (
  <Box sx={{ py: 1 }}>
    <Grid container spacing={2}>
      <Grid item xs={4}>
        <Typography variant="subtitle2" color="textSecondary">
          {label}
        </Typography>
      </Grid>
      <Grid item xs={8}>
        <Typography>{value}</Typography>
      </Grid>
    </Grid>
  </Box>
);

const CustomerDetails: React.FC<Props> = ({ customer, open, onClose, onEdit }) => {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ pb: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            {customer.firstName} {customer.lastName}
          </Typography>
          <Box>
            <Chip
              label={t(`customers.type.${customer.type}`)}
              color={customer.type === 'company' ? 'primary' : 'default'}
              size="small"
              sx={{ mr: 1 }}
            />
            <Chip
              label={t(`customers.status.${customer.status}`)}
              color={customer.status === 'active' ? 'success' : 'error'}
              size="small"
            />
          </Box>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <Typography variant="subtitle1" gutterBottom fontWeight="bold">
            {t('customers.contact_info')}
          </Typography>
          <InfoRow label={t('customers.email')} value={customer.email} />
          <InfoRow label={t('customers.phone')} value={customer.phone} />
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom fontWeight="bold">
            {t('customers.address_info')}
          </Typography>
          <InfoRow label={t('customers.address')} value={customer.address} />
          <InfoRow label={t('customers.city')} value={customer.city} />
          <InfoRow label={t('customers.country')} value={customer.country} />
          
          {customer.type === 'company' && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                {t('customers.company_info')}
              </Typography>
              <InfoRow label={t('customers.company')} value={customer.company || '-'} />
            </>
          )}
          
          {customer.notes && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                {t('customers.notes')}
              </Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {customer.notes}
              </Typography>
            </>
          )}
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom fontWeight="bold">
            {t('customers.system_info')}
          </Typography>
          <InfoRow
            label={t('customers.created_at')}
            value={new Date(customer.createdAt).toLocaleDateString('ar-IL', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          />
          <InfoRow
            label={t('customers.updated_at')}
            value={new Date(customer.updatedAt).toLocaleDateString('ar-IL', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="inherit">
          {t('close')}
        </Button>
        <Button onClick={onEdit} variant="contained" color="primary">
          {t('edit')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CustomerDetails;