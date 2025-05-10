import React from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Typography,
  Chip,
  Button,
  Tooltip,
  TablePagination
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon, Visibility as VisibilityIcon, Add as AddIcon } from '@mui/icons-material';
import { CustomerType } from '../../types/customer';
import { LoadingSpinner } from '../feedback/LoadingSpinner';
import { CustomerFilters } from './CustomerFilters';
import { useNavigate } from 'react-router-dom';

interface CustomerListProps {
  customers: CustomerType[];
  loading: boolean;
  totalItems: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onDelete: (id: number) => void;
  onFilterChange: (filters: any) => void;
}

export const CustomerList: React.FC<CustomerListProps> = ({
  customers,
  loading,
  totalItems,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  onDelete,
  onFilterChange
}) => {
  const navigate = useNavigate();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'warning';
      case 'blocked':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    onPageChange(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    onPageSizeChange(parseInt(event.target.value, 10));
    onPageChange(0);
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h2">
          قائمة العملاء
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => navigate('/customers/new')}
        >
          إضافة عميل جديد
        </Button>
      </Box>

      <CustomerFilters onFilterChange={onFilterChange} />

      <TableContainer component={Paper} sx={{ mt: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>الكود</TableCell>
              <TableCell>الاسم</TableCell>
              <TableCell>الهاتف</TableCell>
              <TableCell>البريد الإلكتروني</TableCell>
              <TableCell>نوع العميل</TableCell>
              <TableCell>الحالة</TableCell>
              <TableCell>الفرع</TableCell>
              <TableCell>الإجراءات</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {customers.map((customer) => (
              <TableRow key={customer.id}>
                <TableCell>{customer.code}</TableCell>
                <TableCell>{customer.name}</TableCell>
                <TableCell dir="ltr">{customer.phone}</TableCell>
                <TableCell>{customer.email || '-'}</TableCell>
                <TableCell>
                  <Chip
                    label={customer.customer_type === 'individual' ? 'فرد' : 
                           customer.customer_type === 'company' ? 'شركة' : 'حكومي'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={customer.status === 'active' ? 'نشط' : 
                           customer.status === 'inactive' ? 'غير نشط' : 'محظور'}
                    color={getStatusColor(customer.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>{customer.branch.name}</TableCell>
                <TableCell>
                  <Tooltip title="عرض التفاصيل">
                    <IconButton
                      size="small"
                      onClick={() => navigate(\`/customers/\${customer.id}\`)}
                    >
                      <VisibilityIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="تعديل">
                    <IconButton
                      size="small"
                      onClick={() => navigate(\`/customers/\${customer.id}/edit\`)}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="حذف">
                    <IconButton
                      size="small"
                      onClick={() => onDelete(customer.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={totalItems}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={pageSize}
        onRowsPerPageChange={handleChangeRowsPerPage}
        labelRowsPerPage="عدد العملاء في الصفحة:"
        labelDisplayedRows={({ from, to, count }) => 
          \`\${from}-\${to} من \${count !== -1 ? count : \`أكثر من \${to}\`}\`
        }
      />
    </Box>
  );
};