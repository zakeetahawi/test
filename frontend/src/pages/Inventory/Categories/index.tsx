import React, { useState } from 'react';
import {
  Box,
  Typography,
  Alert,
  Snackbar,
  Button,
  Paper,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import CategoryList from './CategoryList';
import CategoryForm from './CategoryForm';
import { Category } from '@/types/inventory';
import inventoryService from '@/services/inventoryService';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';

const CategoriesPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
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

  const { data: categories = [] } = useQuery(
    'categories',
    inventoryService.getCategories
  );

  const createMutation = useMutation(
    (data: Omit<Category, 'id' | 'productsCount'>) =>
      inventoryService.createCategory(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('categories');
        setAlert({
          open: true,
          message: t('inventory.success.category_created'),
          severity: 'success',
        });
        setIsFormOpen(false);
      },
      onError: () => {
        setAlert({
          open: true,
          message: t('inventory.error.create_category'),
          severity: 'error',
        });
      },
    }
  );

  const updateMutation = useMutation(
    (data: { id: number; formData: Omit<Category, 'id' | 'productsCount'> }) =>
      inventoryService.updateCategory(data.id, data.formData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('categories');
        setAlert({
          open: true,
          message: t('inventory.success.category_updated'),
          severity: 'success',
        });
        setIsFormOpen(false);
      },
      onError: () => {
        setAlert({
          open: true,
          message: t('inventory.error.update_category'),
          severity: 'error',
        });
      },
    }
  );

  const deleteMutation = useMutation(
    (id: number) => inventoryService.deleteCategory(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('categories');
        setAlert({
          open: true,
          message: t('inventory.success.category_deleted'),
          severity: 'success',
        });
        setIsDeleteDialogOpen(false);
      },
      onError: () => {
        setAlert({
          open: true,
          message: t('inventory.error.delete_category'),
          severity: 'error',
        });
      },
    }
  );

  const handleAdd = () => {
    setSelectedCategory(null);
    setIsFormOpen(true);
  };

  const handleEdit = (category: Category) => {
    setSelectedCategory(category);
    setIsFormOpen(true);
  };

  const handleDelete = (category: Category) => {
    setSelectedCategory(category);
    setIsDeleteDialogOpen(true);
  };

  const handleSubmit = async (data: Omit<Category, 'id' | 'productsCount'>) => {
    if (selectedCategory) {
      await updateMutation.mutateAsync({
        id: selectedCategory.id,
        formData: data,
      });
    } else {
      await createMutation.mutateAsync(data);
    }
  };

  const handleConfirmDelete = async () => {
    if (selectedCategory) {
      await deleteMutation.mutateAsync(selectedCategory.id);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          {t('inventory.categories')}
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleAdd}
        >
          {t('inventory.add_category')}
        </Button>
      </Box>

      <Paper sx={{ p: 2 }}>
        <CategoryList
          categories={categories}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </Paper>

      {isFormOpen && (
        <CategoryForm
          open={isFormOpen}
          onClose={() => setIsFormOpen(false)}
          onSubmit={handleSubmit}
          initialData={selectedCategory || undefined}
          isEdit={!!selectedCategory}
        />
      )}

      <ConfirmDialog
        open={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleConfirmDelete}
        title={t('inventory.delete_category')}
        message={t('inventory.delete_category_confirm')}
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

export default CategoriesPage;