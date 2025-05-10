import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Typography,
  Tooltip
} from '@mui/material';
import { useTranslation } from 'react-i18next';

interface InventoryItem {
  id: number;
  name: string;
  stock: number;
  capacity: number;
  threshold: number;
}

interface Props {
  data: {
    items: InventoryItem[];
  };
}

const InventoryStatus: React.FC<Props> = ({ data }) => {
  const { t } = useTranslation();

  const getStockLevel = (stock: number, capacity: number, threshold: number) => {
    const percentage = (stock / capacity) * 100;
    if (stock <= threshold) return 'error';
    if (percentage <= 30) return 'warning';
    return 'success';
  };

  return (
    <List>
      {data.items.map((item) => {
        const percentage = (item.stock / item.capacity) * 100;
        const color = getStockLevel(item.stock, item.capacity, item.threshold);

        return (
          <ListItem key={item.id}>
            <Box sx={{ width: '100%' }}>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2">{item.name}</Typography>
                <Typography variant="body2" color="textSecondary">
                  {item.stock}/{item.capacity}
                </Typography>
              </Box>
              <Tooltip 
                title={`${percentage.toFixed(1)}% ${t('inventory.utilized')}`}
                arrow
              >
                <LinearProgress
                  variant="determinate"
                  value={percentage}
                  color={color as any}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Tooltip>
              {item.stock <= item.threshold && (
                <Typography 
                  variant="caption" 
                  color="error" 
                  sx={{ display: 'block', mt: 0.5 }}
                >
                  {t('inventory.low_stock_warning')}
                </Typography>
              )}
            </Box>
          </ListItem>
        );
      })}
    </List>
  );
};

export default InventoryStatus;