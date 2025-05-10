import React from 'react';
import { Container, Alert } from '@mui/material';
import { CustomerForm } from '../../components/customers/CustomerForm';
import { CustomerService } from '../../services/customerService';
import { useNavigate, useParams } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { LoadingSpinner } from '../../components/feedback/LoadingSpinner';

export const CustomerFormPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = React.useState(false);
  const [submitLoading, setSubmitLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [customer, setCustomer] = React.useState<any>(null);

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
    if (id) {
      loadCustomer();
    }
  }, [id, loadCustomer]);

  const handleSubmit = async (values: any) => {
    try {
      setSubmitLoading(true);
      if (id) {
        await CustomerService.updateCustomer(parseInt(id), values);
        enqueueSnackbar('تم تحديث بيانات العميل بنجاح', { variant: 'success' });
      } else {
        await CustomerService.createCustomer(values);
        enqueueSnackbar('تم إضافة العميل بنجاح', { variant: 'success' });
      }
      navigate('/customers');
    } catch (err) {
      enqueueSnackbar(
        id ? 'حدث خطأ أثناء تحديث بيانات العميل' : 'حدث خطأ أثناء إضافة العميل',
        { variant: 'error' }
      );
      console.error('Error submitting customer:', err);
    } finally {
      setSubmitLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (id && error) {
    return (
      <Container maxWidth="xl">
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <CustomerForm
        initialValues={customer}
        onSubmit={handleSubmit}
        loading={submitLoading}
      />
    </Container>
  );
};