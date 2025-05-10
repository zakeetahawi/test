import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Paper } from '@mui/material';
import { CustomerForm } from '../../components/customers/CustomerForm';
import { CustomerService, CustomerFormData } from '../../services/customer.service';
import { PageHeader } from '../../components/layout/PageHeader';
import { useAppDispatch } from '../../hooks/redux';
import { showSnackbar } from '../../store/slices/snackbarSlice';

export const CustomerAdd: React.FC = () => {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const navigate = useNavigate();
    const dispatch = useAppDispatch();

    const handleSubmit = async (data: CustomerFormData) => {
        try {
            setIsSubmitting(true);
            await CustomerService.createCustomer(data);
            dispatch(
                showSnackbar({
                    message: 'تم إضافة العميل بنجاح',
                    severity: 'success',
                })
            );
            navigate('/customers');
        } catch (error) {
            dispatch(
                showSnackbar({
                    message: 'حدث خطأ أثناء إضافة العميل',
                    severity: 'error',
                })
            );
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <>
            <PageHeader
                title="إضافة عميل جديد"
                breadcrumbs={[
                    { label: 'الرئيسية', path: '/' },
                    { label: 'العملاء', path: '/customers' },
                    { label: 'إضافة عميل جديد' },
                ]}
            />
            <Paper sx={{ p: 3 }}>
                <CustomerForm
                    onSubmit={handleSubmit}
                    onCancel={() => navigate('/customers')}
                    isSubmitting={isSubmitting}
                />
            </Paper>
        </>
    );
};