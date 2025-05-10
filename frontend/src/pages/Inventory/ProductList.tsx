import React, { useState } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Chip,
  TextField,
  Button,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import HistoryIcon from '@mui/icons-material/History';
import { useTranslation } from 'react-i18next';
import { useQuery } from 'react-query';
import { Product, InventoryFilters } from '@/types/inventory';
import inventoryService from '@/services/inventoryService';

interface Props {
  onView: (product: Product) => void;
  onEdit: (product: Product) => void;
  onDelete: (product: Product) => void;
  onAdd: () => void;
  onViewTransactions: (product: Product) => void;
  categories: { id: string; name: string }[];
}

const ProductList: React.FC<Props> = ({
  onView,
  onEdit,
  onDelete,
  onAdd,
  onViewTransactions,
  categories,
}) => {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<InventoryFilters>({
    page: 0,
    limit: 10,
    search: '',
    category: '',
    stockStatus: 'all',
  });

  const { data, isLoading } = useQuery(
    ['products', filters],
    () => inventoryService.getProducts(filters),
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

  const getStockStatusColor = (product: Product) => {
    if (product.stock <= 0) return 'error';
    if (product.stock <= product.minStock) return 'warning';
    return 'success';
  };

  return (
    <Box>
      <Box 
        display="flex" 
        gap={2} 
        mb={3}
        sx={{
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: { xs: 'stretch', sm: 'center' },
        }}
      >
        <TextField
          placeholder={t('inventory.search')}
          size="small"
          value={filters.search}
          onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value, page: 0 }))}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ flexGrow: 1 }}
        />
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>{t('inventory.category')}</InputLabel>
          <Select
            value={filters.category}
            label={t('inventory.category')}
            onChange={(e) => setFilters((prev) => ({ ...prev, category: e.target.value, page: 0 }))}
          >
            <MenuItem value="">{t('inventory.all_categories')}</MenuItem>
            {categories.map((category) => (
              <MenuItem key={category.id} value={category.id}>
                {category.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>{t('inventory.stock_status')}</InputLabel>
          <Select
            value={filters.stockStatus}
            label={t('inventory.stock_status')}
            onChange={(e) => setFilters((prev) => ({ 
              ...prev, 
              stockStatus: e.target.value as 'all' | 'low' | 'out',
              page: 0
            }))}
          >
            <MenuItem value="all">{t('inventory.all_stock')}</MenuItem>
            <MenuItem value="low">{t('inventory.low_stock')}</MenuItem>
            <MenuItem value="out">{t('inventory.out_of_stock')}</MenuItem>
          </Select>
        </FormControl>

        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={onAdd}
          sx={{ whiteSpace: 'nowrap' }}
        >
          {t('inventory.add_product')}
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('inventory.code')}</TableCell>
              <TableCell>{t('inventory.name')}</TableCell>
              <TableCell>{t('inventory.category')}</TableCell>
              <TableCell align="right">{t('inventory.price')}</TableCell>
              <TableCell align="right">{t('inventory.stock')}</TableCell>
              <TableCell>{t('inventory.status')}</TableCell>
              <TableCell align="right">{t('inventory.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  {t('loading')}
                </TableCell>
              </TableRow>
            ) : data?.products.map((product) => (
              <TableRow key={product.id}>
                <TableCell>{product.code}</TableCell>
                <TableCell>{product.name}</TableCell>
                <TableCell>{product.category}</TableCell>
                <TableCell align="right">₪{product.price.toLocaleString()}</TableCell>
                <TableCell align="right">
                  <Chip
                    label={`${product.stock} ${product.unit}`}
                    color={getStockStatusColor(product)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={t(`inventory.status.${product.status}`)}
                    color={product.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => onEdit(product)}
                    title={t('edit')}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => onViewTransactions(product)}
                    title={t('inventory.view_transactions')}
                  >
                    <HistoryIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => onDelete(product)}
                    title={t('delete')}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={data?.total || 0}
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

export default ProductList;