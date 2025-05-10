import React from 'react';
import { Container, Alert } from '@mui/material';
import { CustomerDetails } from '../../components/customers/CustomerDetails';
import { CustomerService } from '../../services/customerService';
import { useParams, useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { LoadingSpinner } from '../../components/feedback/LoadingSpinner';
import { ConfirmDialog } from '../../components/dialogs/ConfirmDialog';

export const CustomerDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [customer, setCustomer] = React.useState<any>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);

  const loadCustomer = React.useCallback(async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await CustomerService.getCustomer(parseInt(id));
      setCustomer(data);
    } catch (err) {
      setError('حدث خطأ أثناء تحميل بيانات العميل');
      console.error('Error loading customer:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  React.useEffect(() => {
    loadCustomer();
  }, [loadCustomer]);

  const handleAddNote = async (note: string) => {
    try {
      await CustomerService.addNote(parseInt(id!), note);
      enqueueSnackbar('تم إضافة الملاحظة بنجاح', { variant: 'success' });
      loadCustomer(); // إعادة تحميل بيانات العميل لتحديث الملاحظات
    } catch (err) {
      enqueueSnackbar('حدث خطأ أثناء إضافة الملاحظة', { variant: 'error' });
      console.error('Error adding note:', err);
    }
  };

  const handleDelete = async () => {
    try {
      await CustomerService.deleteCustomer(parseInt(id!));
      enqueueSnackbar('تم حذف العميل بنجاح', { variant: 'success' });
      navigate('/customers');
    } catch (err) {
      enqueueSnackbar('حدث خطأ أثناء حذف العميل', { variant: 'error' });
      console.error('Error deleting customer:', err);
    } finally {
      setDeleteDialogOpen(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <Container maxWidth="xl">
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!customer) {
    return (
      <Container maxWidth="xl">
        <Alert severity="warning">لم يتم العثور على العميل</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <CustomerDetails
        customer={customer}
        onAddNote={handleAddNote}
        onDelete={() => setDeleteDialogOpen(true)}
      />

      <ConfirmDialog
        open={deleteDialogOpen}
        title="حذف العميل"
        content="هل أنت متأكد من حذف هذا العميل؟ لا يمكن التراجع عن هذا الإجراء."
        onConfirm={handleDelete}
        onCancel={() => setDeleteDialogOpen(false)}
      />
    </Container>
  );
};