import React, { useState } from 'react';
import { Box, Typography, Alert, Snackbar } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useMutation, useQueryClient } from 'react-query';
import CustomerList from './CustomerList';
import CustomerForm from './CustomerForm';
import CustomerDetails from './CustomerDetails';
import { Customer, CustomerFormData } from '@/types/customer';
import customerService from '@/services/customerService';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';

const CustomersPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [alert, setAlert] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const createMutation = useMutation(customerService.createCustomer, {
    onSuccess: () => {
      queryClient.invalidateQueries('customers');
      setAlert({
        open: true,
        message: t('customers.success.created'),
        severity: 'success',
      });
    },
    onError: () => {
      setAlert({
        open: true,
        message: t('customers.error.create'),
        severity: 'error',
      });
    },
  });

  const updateMutation = useMutation(
    (data: { id: number; data: CustomerFormData }) =>
      customerService.updateCustomer(data.id, data.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('customers');
        setAlert({
          open: true,
          message: t('customers.success.updated'),
          severity: 'success',
        });
      },
      onError: () => {
        setAlert({
          open: true,
          message: t('customers.error.update'),
          severity: 'error',
        });
      },
    }
  );

  const deleteMutation = useMutation(customerService.deleteCustomer, {
    onSuccess: () => {
      queryClient.invalidateQueries('customers');
      setAlert({
        open: true,
        message: t('customers.success.deleted'),
        severity: 'success',
      });
    },
    onError: () => {
      setAlert({
        open: true,
        message: t('customers.error.delete'),
        severity: 'error',
      });
    },
  });

  const handleAdd = () => {
    setSelectedCustomer(null);
    setIsFormOpen(true);
  };

  const handleEdit = (customer: Customer) => {
    setSelectedCustomer(customer);
    setIsFormOpen(true);
  };

  const handleView = (customer: Customer) => {
    setSelectedCustomer(customer);
    setIsDetailsOpen(true);
  };

  const handleDelete = (customer: Customer) => {
    setSelectedCustomer(customer);
    setIsDeleteDialogOpen(true);
  };

  const handleSubmit = async (data: CustomerFormData) => {
    if (selectedCustomer) {
      await updateMutation.mutateAsync({ id: selectedCustomer.id, data });
    } else {
      await createMutation.mutateAsync(data);
    }
    setIsFormOpen(false);
  };

  const handleConfirmDelete = async () => {
    if (selectedCustomer) {
      await deleteMutation.mutateAsync(selectedCustomer.id);
      setIsDeleteDialogOpen(false);
      setSelectedCustomer(null);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {t('customers.title')}
      </Typography>

      <CustomerList
        onView={handleView}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onAdd={handleAdd}
      />

      {isFormOpen && (
        <CustomerForm
          open={isFormOpen}
          onClose={() => setIsFormOpen(false)}
          onSubmit={handleSubmit}
          initialData={selectedCustomer || undefined}
          isEdit={!!selectedCustomer}
        />
      )}

      {isDetailsOpen && selectedCustomer && (
        <CustomerDetails
          open={isDetailsOpen}
          customer={selectedCustomer}
          onClose={() => setIsDetailsOpen(false)}
          onEdit={() => {
            setIsDetailsOpen(false);
            handleEdit(selectedCustomer);
          }}
        />
      )}

      <ConfirmDialog
        open={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleConfirmDelete}
        title={t('customers.delete_title')}
        message={t('customers.delete_message')}
      />

      <Snackbar
        open={alert.open}
        autoHideDuration={6000}
        onClose={() => setAlert({ ...alert, open: false })}
      >
        <Alert
          onClose={() => setAlert({ ...alert, open: false })}
          severity={alert.severity}
          sx={{ width: '100%' }}
        >
          {alert.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CustomersPage;