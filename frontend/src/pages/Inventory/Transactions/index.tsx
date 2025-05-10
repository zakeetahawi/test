import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  InputAdornment,
} from '@mui/material';
import { DateRangePicker } from '@mui/lab';
import SearchIcon from '@mui/icons-material/Search';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { useTranslation } from 'react-i18next';
import { useQuery } from 'react-query';
import { Product, InventoryTransaction } from '@/types/inventory';
import inventoryService from '@/services/inventoryService';

interface TransactionFilters {
  search?: string;
  productId?: number;
  type?: 'in' | 'out' | 'all';
  dateRange?: [Date | null, Date | null];
  page: number;
  limit: number;
}

const TransactionsPage: React.FC = () => {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<TransactionFilters>({
    page: 0,
    limit: 10,
    type: 'all',
  });

  const { data: products = [] } = useQuery(
    'products',
    () => inventoryService.getProducts({ limit: 1000 })
  );

  const { data: transactions, isLoading } = useQuery(
    ['transactions', filters],
    () => inventoryService.getTransactions(filters.productId),
    {
      keepPreviousData: true,
    }
  );

  const handlePageChange = (event: unknown, newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((prev) => ({
      ...prev,
      limit: parseInt(event.target.value, 10),
      page: 0,
    }));
  };

  const handleExport = async () => {
    try {
      const blob = await inventoryService.exportInventory(filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'inventory-transactions.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting transactions:', error);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          {t('inventory.transactions')}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<FileDownloadIcon />}
          onClick={handleExport}
        >
          {t('inventory.export_transactions')}
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="flex-end">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              placeholder={t('inventory.search_transactions')}
              value={filters.search || ''}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, search: e.target.value, page: 0 }))
              }
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>{t('inventory.product')}</InputLabel>
              <Select
                value={filters.productId || ''}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    productId: e.target.value as number,
                    page: 0,
                  }))
                }
                label={t('inventory.product')}
              >
                <MenuItem value="">{t('inventory.all_products')}</MenuItem>
                {products.products?.map((product: Product) => (
                  <MenuItem key={product.id} value={product.id}>
                    {product.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>{t('inventory.transaction_type')}</InputLabel>
              <Select
                value={filters.type || 'all'}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    type: e.target.value as 'in' | 'out' | 'all',
                    page: 0,
                  }))
                }
                label={t('inventory.transaction_type')}
              >
                <MenuItem value="all">{t('inventory.all_transactions')}</MenuItem>
                <MenuItem value="in">{t('inventory.transaction_type.in')}</MenuItem>
                <MenuItem value="out">{t('inventory.transaction_type.out')}</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <DateRangePicker
              value={filters.dateRange || [null, null]}
              onChange={(newValue) =>
                setFilters((prev) => ({
                  ...prev,
                  dateRange: newValue,
                  page: 0,
                }))
              }
              renderInput={(startProps, endProps) => (
                <>
                  <TextField {...startProps} />
                  <Box sx={{ mx: 2 }}> - </Box>
                  <TextField {...endProps} />
                </>
              )}
            />
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('inventory.transaction_date')}</TableCell>
              <TableCell>{t('inventory.product')}</TableCell>
              <TableCell>{t('inventory.transaction_type')}</TableCell>
              <TableCell align="right">{t('inventory.quantity')}</TableCell>
              <TableCell>{t('inventory.reference')}</TableCell>
              <TableCell>{t('inventory.notes')}</TableCell>
              <TableCell>{t('inventory.created_by')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  {t('loading')}
                </TableCell>
              </TableRow>
            ) : (
              transactions?.map((transaction: InventoryTransaction) => (
                <TableRow key={transaction.id}>
                  <TableCell>
                    {new Date(transaction.date).toLocaleDateString('ar-IL', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </TableCell>
                  <TableCell>
                    {products.products?.find((p: Product) => p.id === transaction.productId)?.name}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={t(`inventory.transaction_type.${transaction.type}`)}
                      color={transaction.type === 'in' ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      color={transaction.type === 'in' ? 'success.main' : 'error.main'}
                    >
                      {transaction.type === 'in' ? '+' : '-'}
                      {transaction.quantity}
                    </Typography>
                  </TableCell>
                  <TableCell>{transaction.reference}</TableCell>
                  <TableCell>{transaction.notes}</TableCell>
                  <TableCell>{transaction.createdBy}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={transactions?.length || 0}
          page={filters.page}
          onPageChange={handlePageChange}
          rowsPerPage={filters.limit}
          onRowsPerPageChange={handleRowsPerPageChange}
          labelRowsPerPage={t('table.rows_per_page')}
        />
      </TableContainer>
    </Box>
  );
};

export default TransactionsPage;