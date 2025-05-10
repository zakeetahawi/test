import React from 'react';
import {
  Box,
  Paper,
  Grid,
  Typography,
  Chip,
  Divider,
  Button,
  Stack,
  Card,
  CardContent,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import HistoryIcon from '@mui/icons-material/History';
import { useTranslation } from 'react-i18next';
import { useQuery } from 'react-query';
import { Product } from '@/types/inventory';
import inventoryService from '@/services/inventoryService';

interface Props {
  productId: number;
  onEdit: () => void;
  onViewTransactions: () => void;
}

const ProductDetails: React.FC<Props> = ({
  productId,
  onEdit,
  onViewTransactions,
}) => {
  const { t } = useTranslation();
  
  const { data: product, isLoading } = useQuery(
    ['product', productId],
    () => inventoryService.getProduct(productId)
  );

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>{t('loading')}</Typography>
      </Box>
    );
  }

  if (!product) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">{t('inventory.error.product_not_found')}</Typography>
      </Box>
    );
  }

  const getStockStatusColor = (product: Product) => {
    if (product.stock <= 0) return 'error';
    if (product.stock <= product.minStock) return 'warning';
    return 'success';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            {product.name}
          </Typography>
          <Typography variant="subtitle1" color="textSecondary" gutterBottom>
            {t('inventory.code')}: {product.code}
          </Typography>
          <Chip
            label={t(`inventory.status.${product.status}`)}
            color={product.status === 'active' ? 'success' : 'default'}
            sx={{ mr: 1 }}
          />
          <Chip
            label={product.category}
          />
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<HistoryIcon />}
            onClick={onViewTransactions}
          >
            {t('inventory.view_transactions')}
          </Button>
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={onEdit}
          >
            {t('edit')}
          </Button>
        </Stack>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              {t('inventory.product_details')}
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="body1" color="textSecondary" paragraph>
                  {product.description || t('inventory.no_description')}
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Divider />
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  {t('inventory.unit')}
                </Typography>
                <Typography variant="body1">
                  {product.unit}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  {t('inventory.price')}
                </Typography>
                <Typography variant="body1">
                  ₪{product.price.toLocaleString()}
                </Typography>
              </Grid>
            </Grid>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {t('inventory.stock_limits')}
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  {t('inventory.min_stock')}
                </Typography>
                <Typography variant="body1">
                  {product.minStock} {product.unit}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  {t('inventory.max_stock')}
                </Typography>
                <Typography variant="body1">
                  {product.maxStock} {product.unit}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  {t('inventory.reorder_point')}
                </Typography>
                <Typography variant="body1">
                  {product.minStock} {product.unit}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                {t('inventory.current_stock')}
              </Typography>
              <Typography variant="h3" color={`${getStockStatusColor(product)}.main`}>
                {product.stock}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {product.unit}
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                {t('inventory.stock_value')}
              </Typography>
              <Typography variant="h4">
                ₪{(product.stock * product.price).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                @ ₪{product.price.toLocaleString()} / {product.unit}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProductDetails;