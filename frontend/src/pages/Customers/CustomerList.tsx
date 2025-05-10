import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    IconButton,
    Button,
    TextField,
    Box,
} from '@mui/material';
import {
    Edit as EditIcon,
    Delete as DeleteIcon,
    Add as AddIcon,
} from '@mui/icons-material';
import { CustomerService, Customer, CustomerFilters } from '../../services/customer.service';
import { PageHeader } from '../../components/layout/PageHeader';
import { Loading } from '../../components/feedback/Loading';
import { DeleteConfirmDialog } from '../../components/dialogs/DeleteConfirmDialog';
import { ImportExportActions } from '../../components/customers/ImportExportActions';
import { useAppDispatch } from '../../hooks/redux';
import { showSnackbar } from '../../store/slices/snackbarSlice';

export const CustomerList: React.FC = () => {
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [deleteCustomerId, setDeleteCustomerId] = useState<number | null>(null);
    const navigate = useNavigate();
    const dispatch = useAppDispatch();

    const loadCustomers = async (filters: CustomerFilters = {}) => {
        try {
            setIsLoading(true);
            const response = await CustomerService.getCustomers(filters);
            setCustomers(response.results);
        } catch (error) {
            dispatch(
                showSnackbar({
                    message: 'حدث خطأ أثناء تحميل بيانات العملاء',
                    severity: 'error',
                })
            );
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadCustomers({ search: searchQuery });
    }, [searchQuery]);

    const handleDelete = async () => {
        if (!deleteCustomerId) return;

        try {
            await CustomerService.deleteCustomer(deleteCustomerId);
            setDeleteCustomerId(null);
            dispatch(
                showSnackbar({
                    message: 'تم حذف العميل بنجاح',
                    severity: 'success',
                })
            );
            loadCustomers({ search: searchQuery });
        } catch (error) {
            dispatch(
                showSnackbar({
                    message: 'حدث خطأ أثناء حذف العميل',
                    severity: 'error',
                })
            );
        }
    };

    if (isLoading) {
        return <Loading />;
    }

    return (
        <>
            <PageHeader
                title="العملاء"
                breadcrumbs={[
                    { label: 'الرئيسية', path: '/' },
                    { label: 'العملاء' },
                ]}
                actions={
                    <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => navigate('/customers/add')}
                    >
                        إضافة عميل
                    </Button>
                }
            />

            <Paper sx={{ p: 3, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                    <TextField
                        label="بحث"
                        variant="outlined"
                        size="small"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        sx={{ width: 300 }}
                    />
                    <ImportExportActions
                        filters={{ search: searchQuery }}
                        onImportSuccess={() => loadCustomers({ search: searchQuery })}
                    />
                </Box>

                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>الاسم</TableCell>
                                <TableCell>البريد الإلكتروني</TableCell>
                                <TableCell>رقم الهاتف</TableCell>
                                <TableCell>العنوان</TableCell>
                                <TableCell>الحالة</TableCell>
                                <TableCell align="center">الإجراءات</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {customers.map((customer) => (
                                <TableRow key={customer.id}>
                                    <TableCell>{customer.name}</TableCell>
                                    <TableCell>{customer.email}</TableCell>
                                    <TableCell>{customer.phone}</TableCell>
                                    <TableCell>{customer.address}</TableCell>
                                    <TableCell>
                                        {customer.status === 'active' ? 'نشط' : 'غير نشط'}
                                    </TableCell>
                                    <TableCell align="center">
                                        <IconButton
                                            color="primary"
                                            onClick={() =>
                                                navigate(`/customers/edit/${customer.id}`)
                                            }
                                        >
                                            <EditIcon />
                                        </IconButton>
                                        <IconButton
                                            color="error"
                                            onClick={() => setDeleteCustomerId(customer.id)}
                                        >
                                            <DeleteIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>

            <DeleteConfirmDialog
                open={!!deleteCustomerId}
                title="حذف عميل"
                content="هل أنت متأكد من حذف هذا العميل؟"
                onConfirm={handleDelete}
                onClose={() => setDeleteCustomerId(null)}
            />
        </>
    );
};