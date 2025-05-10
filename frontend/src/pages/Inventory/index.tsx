import React, { useState } from 'react';
import {
  Box,
  Typography,
  Alert,
  Snackbar,
  Grid,
  Card,
  CardContent,
  Stack,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import ProductList from './ProductList';
import ProductForm from './ProductForm';
import TransactionList from './TransactionList';
import TransactionForm from './TransactionForm';
import { Product, ProductFormData } from '@/types/inventory';
import inventoryService from '@/services/inventoryService';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';

const InventoryPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isProductFormOpen, setIsProductFormOpen] = useState(false);
  const [isTransactionListOpen, setIsTransactionListOpen] = useState(false);
  const [isTransactionFormOpen, setIsTransactionFormOpen] = useState(false);
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

  // جلب الفئات
  const { data: categories = [] } = useQuery(
    'categories',
    inventoryService.getCategories
  );

  // جلب إحصائيات المخزون
  const { data: stockStatus } = useQuery(
    'stockStatus',
    inventoryService.getStockStatus
  );

  // إضافة/تعديل منتج
  const productMutation = useMutation(
    (data: { id?: number; formData: ProductFormData }) => {
      if (data.id) {
        return inventoryService.updateProduct(data.id, data.formData);
      }
      return inventoryService.createProduct(data.formData);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('products');
        queryClient.invalidateQueries('stockStatus');
        setAlert({
          open: true,
          message: t(
            selectedProduct
              ? 'inventory.success.product_updated'
              : 'inventory.success.product_created'
          ),
          severity: 'success',
        });
        setIsProductFormOpen(false);
      },
      onError: () => {
        setAlert({
          open: true,
          message: t(
            selectedProduct
              ? 'inventory.error.update_product'
              : 'inventory.error.create_product'
          ),
          severity: 'error',
        });
      },
    }
  );

  // حذف منتج
  const deleteMutation = useMutation(
    (id: number) => inventoryService.deleteProduct(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('products');
        queryClient.invalidateQueries('stockStatus');
        setAlert({
          open: true,
          message: t('inventory.success.product_deleted'),
          severity: 'success',
        });
        setIsDeleteDialogOpen(false);
      },
      onError: () => {
        setAlert({
          open: true,
          message: t('inventory.error.delete_product'),
          severity: 'error',
        });
      },
    }
  );

  // إضافة معاملة
  const transactionMutation = useMutation(
    (data: { productId: number; type: 'in' | 'out'; quantity: number; reference: string; notes?: string }) =>
      inventoryService.addTransaction(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('products');
        queryClient.invalidateQueries('transactions');
        queryClient.invalidateQueries('stockStatus');
        setAlert({
          open: true,
          message: t('inventory.success.transaction_added'),
          severity: 'success',
        });
        setIsTransactionFormOpen(false);
      },
      onError: () => {
        setAlert({
          open: true,
          message: t('inventory.error.add_transaction'),
          severity: 'error',
        });
      },
    }
  );

  const handleAddProduct = () => {
    setSelectedProduct(null);
    setIsProductFormOpen(true);
  };

  const handleEditProduct = (product: Product) => {
    setSelectedProduct(product);
    setIsProductFormOpen(true);
  };

  const handleDeleteProduct = (product: Product) => {
    setSelectedProduct(product);
    setIsDeleteDialogOpen(true);
  };

  const handleViewTransactions = (product: Product) => {
    setSelectedProduct(product);
    setIsTransactionListOpen(true);
  };

  const handleSubmitProduct = async (formData: ProductFormData) => {
    await productMutation.mutateAsync({
      id: selectedProduct?.id,
      formData,
    });
  };

  const handleConfirmDelete = async () => {
    if (selectedProduct) {
      await deleteMutation.mutateAsync(selectedProduct.id);
    }
  };

  const handleAddTransaction = () => {
    setIsTransactionListOpen(false);
    setIsTransactionFormOpen(true);
  };

  const handleSubmitTransaction = async (data: {
    type: 'in' | 'out';
    quantity: number;
    reference: string;
    notes?: string;
  }) => {
    if (selectedProduct) {
      await transactionMutation.mutateAsync({
        productId: selectedProduct.id,
        ...data,
      });
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {t('inventory.title')}
      </Typography>

      {stockStatus && (
        <Grid container spacing={2} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Stack spacing={1}>
                  <Typography variant="subtitle2" color="textSecondary">
                    {t('inventory.total_products')}
                  </Typography>
                  <Typography variant="h4">
                    {stockStatus.totalProducts}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Stack spacing={1}>
                  <Typography variant="subtitle2" color="textSecondary">
                    {t('inventory.low_stock_products')}
                  </Typography>
                  <Typography variant="h4" color="warning.main">
                    {stockStatus.lowStockProducts}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Stack spacing={1}>
                  <Typography variant="subtitle2" color="textSecondary">
                    {t('inventory.out_of_stock_products')}
                  </Typography>
                  <Typography variant="h4" color="error.main">
                    {stockStatus.outOfStockProducts}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Stack spacing={1}>
                  <Typography variant="subtitle2" color="textSecondary">
                    {t('inventory.total_value')}
                  </Typography>
                  <Typography variant="h4">
                    ₪{stockStatus.totalValue.toLocaleString()}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <ProductList
        onView={handleViewTransactions}
        onEdit={handleEditProduct}
        onDelete={handleDeleteProduct}
        onAdd={handleAddProduct}
        onViewTransactions={handleViewTransactions}
        categories={categories}
      />

      {isProductFormOpen && (
        <ProductForm
          open={isProductFormOpen}
          onClose={() => setIsProductFormOpen(false)}
          onSubmit={handleSubmitProduct}
          initialData={selectedProduct || undefined}
          isEdit={!!selectedProduct}
          categories={categories}
        />
      )}

      {isTransactionListOpen && selectedProduct && (
        <TransactionList
          open={isTransactionListOpen}
          onClose={() => setIsTransactionListOpen(false)}
          product={selectedProduct}
          onAddTransaction={handleAddTransaction}
        />
      )}

      {isTransactionFormOpen && selectedProduct && (
        <TransactionForm
          open={isTransactionFormOpen}
          onClose={() => setIsTransactionFormOpen(false)}
          onSubmit={handleSubmitTransaction}
          product={selectedProduct}
        />
      )}

      <ConfirmDialog
        open={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleConfirmDelete}
        title={t('inventory.delete_product')}
        message={t('inventory.delete_product_confirm')}
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

export default InventoryPage;