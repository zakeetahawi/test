import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Paper } from '@mui/material';
import { CustomerForm } from '../../components/customers/CustomerForm';
import { CustomerService, CustomerFormData, Customer } from '../../services/customer.service';
import { PageHeader } from '../../components/layout/PageHeader';
import { useAppDispatch } from '../../hooks/redux';
import { showSnackbar } from '../../store/slices/snackbarSlice';
import { Loading } from '../../components/feedback/Loading';

export const CustomerEdit: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [customer, setCustomer] = useState<Customer | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const navigate = useNavigate();
    const dispatch = useAppDispatch();

    useEffect(() => {
        loadCustomer();
    }, [id]);

    const loadCustomer = async () => {
        if (!id) return;
        try {
            setIsLoading(true);
            const data = await CustomerService.getCustomer(parseInt(id));
            setCustomer(data);
        } catch (error) {
            dispatch(
                showSnackbar({
                    message: 'حدث خطأ أثناء تحميل بيانات العميل',
                    severity: 'error',
                })
            );
            navigate('/customers');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = async (data: CustomerFormData) => {
        if (!id) return;
        try {
            setIsSubmitting(true);
            await CustomerService.updateCustomer(parseInt(id), data);
            dispatch(
                showSnackbar({
                    message: 'تم تحديث بيانات العميل بنجاح',
                    severity: 'success',
                })
            );
            navigate('/customers');
        } catch (error) {
            dispatch(
                showSnackbar({
                    message: 'حدث خطأ أثناء تحديث بيانات العميل',
                    severity: 'error',
                })
            );
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) {
        return <Loading />;
    }

    if (!customer) {
        return null;
    }

    return (
        <>
            <PageHeader
                title={`تحرير العميل: ${customer.name}`}
                breadcrumbs={[
                    { label: 'الرئيسية', path: '/' },
                    { label: 'العملاء', path: '/customers' },
                    { label: 'تحرير العميل' },
                ]}
            />
            <Paper sx={{ p: 3 }}>
                <CustomerForm
                    initialData={customer}
                    onSubmit={handleSubmit}
                    onCancel={() => navigate('/customers')}
                    isSubmitting={isSubmitting}
                />
            </Paper>
        </>
    );
};