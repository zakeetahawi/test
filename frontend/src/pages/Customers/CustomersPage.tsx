import React from 'react';
import { Container, Alert } from '@mui/material';
import { CustomerList } from '../../components/customers/CustomerList';
import { CustomerService } from '../../services/customerService';
import { CustomerFilters, CustomerType } from '../../types/customer';
import { useSnackbar } from 'notistack';
import { ConfirmDialog } from '../../components/dialogs/ConfirmDialog';

export const CustomersPage: React.FC = () => {
  const [customers, setCustomers] = React.useState<CustomerType[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [totalItems, setTotalItems] = React.useState(0);
  const [page, setPage] = React.useState(0);
  const [pageSize, setPageSize] = React.useState(10);
  const [filters, setFilters] = React.useState<CustomerFilters>({});
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [customerToDelete, setCustomerToDelete] = React.useState<number | null>(null);
  const { enqueueSnackbar } = useSnackbar();

  const loadCustomers = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await CustomerService.getCustomers({
        ...filters,
        page: page + 1,
        page_size: pageSize
      });
      setCustomers(data.results);
      setTotalItems(data.count);
    } catch (err) {
      setError('حدث خطأ أثناء تحميل بيانات العملاء');
      console.error('Error loading customers:', err);
    } finally {
      setLoading(false);
    }
  }, [filters, page, pageSize]);

  React.useEffect(() => {
    loadCustomers();
  }, [loadCustomers]);

  const handleFilterChange = (newFilters: CustomerFilters) => {
    setFilters(newFilters);
    setPage(0);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
  };

  const handleDeleteClick = (customerId: number) => {
    setCustomerToDelete(customerId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (customerToDelete) {
      try {
        await CustomerService.deleteCustomer(customerToDelete);
        enqueueSnackbar('تم حذف العميل بنجاح', { variant: 'success' });
        loadCustomers();
      } catch (err) {
        enqueueSnackbar('حدث خطأ أثناء حذف العميل', { variant: 'error' });
        console.error('Error deleting customer:', err);
      } finally {
        setDeleteDialogOpen(false);
        setCustomerToDelete(null);
      }
    }
  };

  return (
    <Container maxWidth="xl">
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <CustomerList
        customers={customers}
        loading={loading}
        totalItems={totalItems}
        page={page}
        pageSize={pageSize}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        onDelete={handleDeleteClick}
        onFilterChange={handleFilterChange}
      />

      <ConfirmDialog
        open={deleteDialogOpen}
        title="حذف العميل"
        content="هل أنت متأكد من حذف هذا العميل؟ لا يمكن التراجع عن هذا الإجراء."
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteDialogOpen(false)}
      />
    </Container>
  );
};