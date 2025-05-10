import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  LinearProgress,
  Stack,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useQuery } from 'react-query';
import inventoryService from '@/services/inventoryService';

const InventoryMetrics: React.FC = () => {
  const { t } = useTranslation();
  
  const { data: stockStatus, isLoading } = useQuery(
    'stockStatus',
    inventoryService.getStockStatus
  );

  if (isLoading) {
    return <LinearProgress />;
  }

  if (!stockStatus) {
    return null;
  }

  const calculateUtilization = () => {
    if (stockStatus.totalProducts === 0) return 0;
    const utilizedProducts = stockStatus.totalProducts - stockStatus.outOfStockProducts;
    return (utilizedProducts / stockStatus.totalProducts) * 100;
  };

  const utilizationPercentage = calculateUtilization();

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6" gutterBottom>
                {t('inventory.stock_overview')}
              </Typography>
              
              <Box>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2" color="textSecondary">
                    {t('inventory.utilized')}
                  </Typography>
                  <Typography variant="body2">
                    {utilizationPercentage.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={utilizationPercentage}
                  color={utilizationPercentage < 50 ? 'warning' : 'primary'}
                />
              </Box>

              <Box>
                <Typography color="error" variant="body2" gutterBottom>
                  {stockStatus.lowStockProducts > 0 &&
                    t('inventory.low_stock_warning', {
                      count: stockStatus.lowStockProducts,
                    })}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('inventory.quick_stats')}
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  {t('inventory.items_count')}
                </Typography>
                <Typography variant="h4">
                  {stockStatus.totalProducts}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  {t('inventory.total_value')}
                </Typography>
                <Typography variant="h4">
                  ₪{stockStatus.totalValue.toLocaleString()}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  {t('inventory.low_stock')}
                </Typography>
                <Typography
                  variant="h5"
                  color={stockStatus.lowStockProducts > 0 ? 'warning.main' : 'inherit'}
                >
                  {stockStatus.lowStockProducts}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  {t('inventory.out_of_stock')}
                </Typography>
                <Typography
                  variant="h5"
                  color={stockStatus.outOfStockProducts > 0 ? 'error.main' : 'inherit'}
                >
                  {stockStatus.outOfStockProducts}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default InventoryMetrics;